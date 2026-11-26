"""
Movement Service Module

Every change to the quantity of a lot goes through record_movement().
It applies the change to the lot and saves the StockMovement to keep a trace of it,
the same way for every type: (RESTOCK, DEDUCTION, RETURN, ADJUSTMENT).

Each kind of change keeps its own route and service (different roles, data and rules),
only this last step is shared.

This module also reads the movement history (Manager only).

Author: Zacchary Bedard-Chenier
Date: 21/11/2026
Version: 1.0
"""

from datetime import datetime, time, timedelta

from sqlalchemy import select

from ..models import LotStock, StockMovement
from .errors import InvalidOperationError

MAX_MOVEMENTS = 500  # the most movements a single read can return when reading or filtering the movements history


def record_movement(session, lot, change, movement_type, user_id=None,
                    order_id=None, button_press_id=None, reason=None):
    """Applies a +/- change to a lot and save the movement. Does not commit.

    The caller must have locked the lot (with_for_update) if other requests can change it.

    Args:
        session: The database session of the request.
        lot (LotStock): The lot to change.
        change (Decimal): Negative = the stock goes down
                          positive = the stock goes up.
        movement_type (MovementType): Why the quantity changes.
        user_id (int, optional): The id of the user making the change.
        order_id (int, optional): The id of the client order (DEDUCTION and RETURN only).
        button_press_id (str, optional): Id of the + or - press on the POS (DEDUCTION and RETURN only).
        reason (str, optional): Why the stock is changed (ADJUSTMENT).

    Returns:
        The new StockMovement.

    Raises:
        InvalidOperationError: If the lot would hold a negative quantity.
    """
    # the quantity of a lot can never become negative
    if lot._quantity + change < 0:
        raise InvalidOperationError(
            f'Lot with id "{lot._id}" holds {lot._quantity}, it cannot be changed by {change}.'
        )

    lot._quantity += change

    movement = StockMovement(
        _lot_stock_id=lot._id,
        _type=movement_type,
        _quantity_change=change,
        _order_id=order_id,
        _button_press_id=button_press_id,
        _reason=reason,
        _user_id=user_id
    )
    session.add(movement)

    return movement


def list_movements(session, movement_type=None, ingredient_id=None, lot_stock_id=None,
                   order_id=None, date_from=None, date_to=None, limit=100):
    """Returns the movements that match every filter given, the newest first.

    Args:
        session: The database session of the request.
        movement_type (MovementType, optional): Only this type of movement.
        ingredient_id (int, optional): Only the lots of this ingredient.
        lot_stock_id (int, optional): Only this lot.
        order_id (int, optional): Only this client order.
        date_from (date, optional): From this day (included).
        date_to (date, optional): Up to this day (included).
        limit (int): The most movements returned (max MAX_MOVEMENTS).

    Returns:
        A list of StockMovement.
    """
    query = select(StockMovement)

    # checks the filters passed in argument
    if movement_type is not None:
        query = query.where(StockMovement._type == movement_type)
    if ingredient_id is not None:
        # the ingredient is on the lot, not on the movement
        query = query.join(LotStock, LotStock._id == StockMovement._lot_stock_id)
        query = query.where(LotStock._ingredient_id == ingredient_id)
    if lot_stock_id is not None:
        query = query.where(StockMovement._lot_stock_id == lot_stock_id)
    if order_id is not None:
        query = query.where(StockMovement._order_id == order_id)
    if date_from is not None:
        query = query.where(StockMovement._created_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        # before the start of the next day, so the whole last day is included
        # for eample, if date_to = 2026-11-20, then 2026-11-20 is included in full
        # This is needed because _created_at is date AND time, so they can't be directly compared
        query = query.where(StockMovement._created_at < datetime.combine(date_to + timedelta(days=1), time.min))

    query = query.order_by(StockMovement._id.desc()).limit(min(limit, MAX_MOVEMENTS))

    return list(session.scalars(query))
