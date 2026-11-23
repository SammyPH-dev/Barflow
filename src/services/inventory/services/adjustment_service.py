"""
Adjustment Service Module

This module contains the business logic of the manual stock changes.
Adjustments of a lot: a loss (breakage, spoilage, spill...) or a correction after a physical count.

Only a Manager can do this, the role is checked in the route.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from sqlalchemy import select

from ..models import Ingredient, LotStock, MovementType
from . import movement_service, stock_service
from .errors import NotFoundError


def adjust_lot(session, data, user_id=None, today=None):
    """Change the quantity of a lot with a +/- change.

    A negative change is a loss (breakage, spoilage, spill...), a positive one is a correction
    (ex: more stock found after a physical count). Both are saved as an ADJUSTMENT movement.

    Args:
        session: The database session of the request (SQLAlchemy object).
        data (AdjustmentDbSchema): The validated adjustment.
        user_id (int, optional): The id of the Manager.
        today (date, optional): Date used for the stock levels. Defaults to today.

    Returns:
        A tuple (movement, alert). alert is None unless a threshold was crossed.

    Raises:
        NotFoundError: If the lot does not exist.
        InvalidOperationError: If the lot would hold a negative quantity.
    """
    # lock the row of the lot so nobody else changes it at the same time
    query = select(LotStock).where(LotStock._id == data.lot_stock_id).with_for_update()
    lot = session.scalars(query).first()
    if lot is None:
        raise NotFoundError(f'Lot with id "{data.lot_stock_id}" not found.')

    ingredient = session.get(Ingredient, lot._ingredient_id)

    # stock of the ingredient before the change (to know if the threshold gets crossed)
    level_before = stock_service.get_stock_level(session, lot._ingredient_id, today)

    movement = movement_service.record_movement(
        session, lot, data.quantity_change, MovementType.ADJUSTMENT,
        user_id=user_id, reason=data.reason
    )

    # stock of the ingredient after the change
    level_after = stock_service.get_stock_level(session, lot._ingredient_id, today)

    # an alert is only created if we just went under the reorder threshold
    alert = None
    if stock_service.crossed_threshold(
        level_before['usable_quantity'],
        level_after['usable_quantity'],
        ingredient._reorder_threshold
    ):
        alert = stock_service.alert_from_level(level_after)

    return movement, alert
