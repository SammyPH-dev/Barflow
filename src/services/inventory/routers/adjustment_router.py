"""
Adjustment Routes Module

This module implements the REST endpoint for the manual stock changes made by a Manager:
a loss (breakage, spoilage, spill) or a correction after a physical count.
Client orders (+ / - on the POS) are in stock_router.py, supplier orders in restock_router.py.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database_connection import get_session
from ..permissions import manager_required
from ..schemas.stock_update import AdjustmentDbSchema
from ..services import adjustment_service
from .router_utils import alert_json, error_response, movement_json

router = APIRouter(tags=['adjustments'])


def adjustment_json(movement, alert):
    # the movement saved for the change, and the alert if the threshold was just crossed
    return {
        'movement': movement_json(movement),
        'alert': alert_json(alert) if alert is not None else None
    }


# adjust_lot()
@router.post('/adjustments')
def adjust_lot(data: AdjustmentDbSchema,
               session: Session = Depends(get_session),
               manager: dict = Depends(manager_required)):
    """Change the quantity of a lot: a negative change is a loss (breakage, spoilage, missing items...),
    a positive one is a correction (for example after a physical count).

    Args:
        None. The adjustment is obtained from the JSON request body containing:
            - lot_stock_id (int): The id of the lot.
            - quantity_change (decimal): The change, + or - (cannot be 0).
            - reason (str): Why the stock is changed.

    Returns:
        A JSON object containing the movement and the alert (or null) and HTTP 201 (Created).
        On error: JSON error message and appropriate HTTP status code
        (403 not a Manager, 404 unknown lot, 409 more than the lot holds,
        422 invalid data, 500 server error).
    """
    try:
        movement, alert = adjustment_service.adjust_lot(session, data, user_id=manager['id'])
        session.commit()

        return JSONResponse(adjustment_json(movement, alert), status_code=201)
    except Exception as e:
        return error_response(session, e, f'adjusting the lot with id "{data.lot_stock_id}"')
