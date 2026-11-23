"""
Supplier Order Service Module

This module contains the business logic of the supplier orders (Manager only).

An order can have as many lines (ingredients) as needed. Each line becomes one lot,
and a lot contains a single ingredient. Every restock is a supplier order.

The expiry date of a lot is calculated from the shelf life of its ingredient.
Ex: a lot of an ingredient that lasts 7 days, received on the 1st, expires on the 8th.
An ingredient without a shelf life never expires.

For the purposes of this project, an order is received immediately.
When "Order" is pressed on the POS, the order is saved and all its lots are added to the inventory at once.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import (
    Ingredient, LigneSupplierOrder, LotStock, MovementType, SupplierOrder, SupplierOrderStatus,
)
from . import movement_service
from .errors import NotFoundError

# Money is rounded to the cent
CENT = Decimal('0.01')


def get_order(session, order_id):
    """Returns one supplier order with its lines (NotFoundError if it does not exist)."""
    query = (
        select(SupplierOrder)
        .where(SupplierOrder._id == order_id)
        .options(selectinload(SupplierOrder._lines))
    )

    order = session.scalars(query).first()
    if order is None:
        raise NotFoundError(f'Supplier order with id "{order_id}" not found.')

    return order


def get_all_orders(session):
    """Return every supplier order with its lines, newest first."""
    query = (
        select(SupplierOrder)
        .options(selectinload(SupplierOrder._lines))
        .order_by(SupplierOrder._id.desc())
    )
    return list(session.scalars(query))


def create_order(session, data, manager_id, today=None):
    """Creates a supplier order and the inventory receives it immediately.

    One lot and one RESTOCK movement is created for each line, so the stock
    goes up right away. The expiry date of each lot is calculated from the shelf life
    of its ingredient (ex: milk lasts 7 days, so it expires 7 days after the order day).
    Everything is saved together: if one line is refused, the route cancels the whole order
    (all or nothing).

    Args:
        session: The database session of the request.
        data (SupplierOrderDbSchema): The validated order and its lines.
        manager_id (int): The id of the Manager placing the order.
        today (date, optional): The reception date of the lots. Defaults to today.

    Returns:
        The new SupplierOrder, with the status RECEIVED.

    Raises:
        NotFoundError: If one of the ingredients does not exist.
    """
    if today is None:
        today = date.today()

    ingredients = load_ingredients(session, data)

    # the lines are saved sorted by ingredient name, so they are always returned in that order
    # lower() so the sort ignores the case, like MariaDB does
    sorted_lines = sorted(data.lines, key=lambda line: ingredients[line.ingredient_id]._name.lower())

    lines = []
    for line in sorted_lines:
        lines.append(LigneSupplierOrder(
            _ingredient_id=line.ingredient_id,
            _quantity=line.quantity,
            _unit_price=line.unit_price
        ))

    order = SupplierOrder(
        _placed_by=manager_id,
        _status=SupplierOrderStatus.RECEIVED,
        _total=compute_total(data),
        _lines=lines
    )
    session.add(order)

    for order_line in order._lines:
        lot = create_lot(
            session,
            ingredient=ingredients[order_line._ingredient_id],
            quantity=order_line._quantity,
            reception_date=today,
            user_id=manager_id
        )
        order_line._lot_stock_id = lot._id

    return order


# private helpers of this module


def load_ingredients(session, data):
    """Loads the ingredients of the order lines as {id: Ingredient}.

    Raises NotFoundError if a line uses an ingredient that does not exist.
    """
    wanted_ids = {line.ingredient_id for line in data.lines}

    query = select(Ingredient).where(Ingredient._id.in_(wanted_ids))
    ingredients = {ingredient._id: ingredient for ingredient in session.scalars(query)}

    missing = wanted_ids - set(ingredients)
    if missing:
        raise NotFoundError(f'Unknown ingredient(s): {sorted(missing)}.')

    return ingredients


def compute_total(data):
    """Total of the order. Each line is rounded to the cent before being added."""
    total = Decimal('0.00')

    for line in data.lines:
        total += (line.quantity * line.unit_price).quantize(CENT, ROUND_HALF_UP)

    return total


def create_lot(session, ingredient, quantity, reception_date, user_id):
    """Creates the lot of one order line and saves a RESTOCK movement for it."""
    # the lot starts empty, the RESTOCK movement below adds the quantity received
    lot = LotStock(
        _ingredient_id=ingredient._id,
        _quantity=Decimal(0),
        _reception_date=reception_date,
        _exp_date=calculate_exp_date(ingredient, reception_date)
    )
    session.add(lot)
    # flush sends the INSERT without committing, so the lot gets its _id
    session.flush()

    movement_service.record_movement(session, lot, quantity, MovementType.RESTOCK, user_id=user_id)

    return lot


def calculate_exp_date(ingredient, reception_date):
    """Return the day the lot expires: reception date + shelf life of the ingredient.

    Returns None (never expires) if the ingredient has no shelf life.
    """
    if ingredient._shelf_life_days is None:
        return None

    return reception_date + timedelta(days=ingredient._shelf_life_days)
