"""
Client Order Service Module

This module takes the stock needed when an item is added to a client order (+ on the POS),
and gives it back when an item is removed (- on the POS).
It is called by the order service (client orders, not supplier orders).

Business rules:
- check + deducts ALL the ingredients of the item (recipe) in one transaction
  and lock the row until the change has been registered
- only the usable lots count (quantity > 0 and not expired);
- the lots that expire first are used first;
- a removed item goes back to the same lots it was taken from.

The functions never commit. The route commits once everything worked.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from ..models import Ingredient, LotStock, MovementType, StockMovement
from . import movement_service, stock_service
from .errors import InvalidOperationError, NotFoundError


def deduct(session, data, user_id=None, today=None):
    """Deduct all the ingredients of an item added to a client order (+ on the POS), or nothing gets deducted.

    If the stock is not enough, success is False with the list of shortages:
    the POS shows the "not enough stock" warning and the item is not added.
    If the same button press id is sent again (offline POS sending again),
    success is True but nothing is deducted a second time.

    Args:
        session: The database session of the request.
        data (DeductionDbSchema): The validated order id, button press id and ingredients.
        user_id (int, optional): The id of the user adding the item.
        today (date, optional): Date used to know if a lot is expired. Defaults to today.

    Returns:
        A dict: {'order_id', 'success', 'shortages', 'alerts'}.

    Raises:
        NotFoundError: If one of the ingredients does not exist.
    """
    if today is None:
        today = date.today()

    # if the same press was already processed = nothing to do
    if press_already_processed(session, data.button_press_id, MovementType.DEDUCTION):
        return {'order_id': data.order_id, 'success': True, 'shortages': [], 'alerts': []}

    # loads what it needs
    ingredient_ids = sorted(item.ingredient_id for item in data.items)
    ingredients = load_ingredients(session, ingredient_ids)
    lots_by_ingredient = load_and_lock_lots(session, ingredient_ids, today)
    available = compute_available(ingredient_ids, lots_by_ingredient)

    # checks everything first. If only one ingredient is short, nothing is written
    shortages = find_shortages(data, available)
    if shortages:
        return {'order_id': data.order_id, 'success': False, 'shortages': shortages, 'alerts': []}

    # if everything is available, it deducts
    alerts = []
    for item in data.items:
        take_from_lots(session, item.quantity, lots_by_ingredient[item.ingredient_id], data, user_id)

        # checks if this deduction brings any ingredient under its reorder threshold?
        ingredient = ingredients[item.ingredient_id]
        before = available[item.ingredient_id]
        after = before - item.quantity
        if stock_service.crossed_threshold(before, after, ingredient._reorder_threshold):
            alerts.append(stock_service.alert_from_ingredient(ingredient, after))

    return {'order_id': data.order_id, 'success': True, 'shortages': [], 'alerts': alerts}


def return_items(session, data, user_id=None):
    """Give back the ingredients of an item removed from a client order (- on the POS).

    The quantities go back to the SAME lots the client order took them from,
    starting with the lots it used last. Calling it again with the same
    button press id is safe: nothing is given back a second time.

    The order service processes only one + or - at a time for the same order.

    Args:
        session: The database session of the request.
        data (ReturnDbSchema): The validated order id, button press id and ingredients.
        user_id (int, optional): The id of the user removing the item.

    Raises:
        NotFoundError: If one of the ingredients does not exist.
        InvalidOperationError: If the order never took that much of an ingredient.
    """
    # if the same press was already processed = nothing to do
    if press_already_processed(session, data.button_press_id, MovementType.RETURN):
        return

    # checks what the order still holds from each lot, for each ingredient
    ingredient_ids = sorted(item.ingredient_id for item in data.items)
    load_ingredients(session, ingredient_ids)
    taken = get_taken_by_lot(session, data.order_id, ingredient_ids)

    # checks that an order will not give back more than it took
    for item in data.items:
        still_taken = sum(quantity for lot_id, quantity in taken[item.ingredient_id])
        if still_taken < item.quantity:
            raise InvalidOperationError(
                f'Order with id "{data.order_id}" only holds {still_taken} of the ingredient '
                f'with id "{item.ingredient_id}", it cannot give back {item.quantity}.'
            )

    # locks the lots, always in the same order (by id) to avoid deadlocks during execution
    lot_ids = sorted({lot_id for lots in taken.values() for lot_id, _ in lots})
    query = select(LotStock).where(LotStock._id.in_(lot_ids)).order_by(LotStock._id).with_for_update()
    lots = {lot._id: lot for lot in session.scalars(query)}

    # gives back the proper quantity, lot by lot
    for item in data.items:
        remaining = item.quantity
        for lot_id, still_taken in taken[item.ingredient_id]:
            if remaining == 0:
                break

            # the quantity is given back even if the lot expired in the meantime:
            # expired lots are already ignored when the usable stock is counted anyways,
            # so those ingredients back in the inventory will not be used (on their own or in a recipe)
            given = min(still_taken, remaining)
            remaining -= given

            movement_service.record_movement(
                session, lots[lot_id], given, MovementType.RETURN, user_id=user_id,
                order_id=data.order_id, button_press_id=data.button_press_id
            )


# helpers of this module


def get_taken_by_lot(session, order_id, ingredient_ids):
    """
    For one order, return {ingredient_id: [(lot_id, quantity still taken), ...]}.
    All the DEDUCTION and RETURN movements of the order are added together per lot.
    The lots used last come first, so a removed item goes back where the last one came from.
    A lot that was fully given back (total 0) is skipped.
    """
    query = (
        select(
            StockMovement._lot_stock_id,
            LotStock._ingredient_id,
            func.sum(StockMovement._quantity_change),
            func.max(StockMovement._id),
        )
        .join(LotStock, LotStock._id == StockMovement._lot_stock_id)
        .where(
            StockMovement._order_id == order_id,
            StockMovement._type.in_([MovementType.DEDUCTION, MovementType.RETURN]),
            LotStock._ingredient_id.in_(ingredient_ids),
        )
        .group_by(StockMovement._lot_stock_id, LotStock._ingredient_id)
        .order_by(func.max(StockMovement._id).desc())
    )

    taken = defaultdict(list)
    for lot_id, ingredient_id, total, _ in session.execute(query).all():
        # a deduction is saved as a negative number, so the total is negated
        still_taken = -Decimal(total)
        if still_taken > 0:
            taken[ingredient_id].append((lot_id, still_taken))

    return taken


def press_already_processed(session, button_press_id, movement_type):
    # True if a movement of this type with this button press id already exists
    query = select(StockMovement._id).where(
        StockMovement._button_press_id == button_press_id,
        StockMovement._type == movement_type,
    ).limit(1)
    return session.execute(query).first() is not None


def load_ingredients(session, ingredient_ids):
    # Loads the ingredients of the order as {id: Ingredient}
    # NotFoundError if one is missing
    query = select(Ingredient).where(Ingredient._id.in_(ingredient_ids))
    ingredients = {ingredient._id: ingredient for ingredient in session.scalars(query)}

    missing = set(ingredient_ids) - set(ingredients)
    if missing:
        raise NotFoundError(f'Unknown ingredient(s): {sorted(missing)}.')

    return ingredients


def load_and_lock_lots(session, ingredient_ids, today):
    """
    Loads and locks the usable lots of the ingredients, grouped by ingredient.

    The sort order is always the same (ingredient, expiry, id). This way, two orders
    validated at the same time lock the rows in the same order, which avoids deadlocks.
    It is also the order the lots are used in: the ones that expire first are used first.
    """
    query = (
        select(LotStock)
        .where(
            LotStock._ingredient_id.in_(ingredient_ids),
            stock_service.usable_lot_filter(today),
        )
        .order_by(
            LotStock._ingredient_id,
            LotStock._exp_date.is_(None), # the lots with no expiry date go last
            LotStock._exp_date,
            LotStock._id,
        )
        .with_for_update()
    )

    lots_by_ingredient = defaultdict(list)
    for lot in session.scalars(query).all():
        lots_by_ingredient[lot._ingredient_id].append(lot)

    return lots_by_ingredient


def compute_available(ingredient_ids, lots_by_ingredient):
    # Returns {ingredient_id: total quantity of its usable lots}
    available = {}

    for ingredient_id in ingredient_ids:
        total = Decimal(0)
        for lot in lots_by_ingredient[ingredient_id]:
            total += lot._quantity
        available[ingredient_id] = total

    return available


def find_shortages(data, available):
    # Lists the ingredients that don't have enough stock for the order
    shortages = []

    for item in data.items:
        if available[item.ingredient_id] < item.quantity:
            shortages.append({
                'ingredient_id': item.ingredient_id,
                'requested': item.quantity,
                'available': available[item.ingredient_id]
            })

    return shortages


def take_from_lots(session, quantity, lots, data, user_id):
    # Takes "quantity" from the lots and saves a movement for each lot modified
    remaining = quantity

    for lot in lots:
        if remaining == 0:
            break

        # takes what is needed, or the whole lot if it's not enough
        taken = min(lot._quantity, remaining)
        remaining -= taken

        movement_service.record_movement(
            session, lot, -taken, MovementType.DEDUCTION, user_id=user_id,
            order_id=data.order_id, button_press_id=data.button_press_id
        )
