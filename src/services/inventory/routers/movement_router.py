"""
Movement Routes Module

This module implements the REST endpoint that reads the history of the stock movements
(restocks, client order deductions and returns, manual adjustments), Manager only.

The movements are only written by their own routes (restock_router, stock_router,
adjustment_router), this one only reads them.

Author: Zacchary Bedard-Chenier
Date: 21/11/2026
Version: 1.0
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database_connection import get_session
from ..permissions import manager_required
from ..models import MovementType
from ..services import movement_service
from .router_utils import error_response, movement_json

router = APIRouter(tags=['movements'])


# get_all_movements()
@router.get('/movements')
def get_all_movements(type: MovementType | None = None,
                      ingredient_id: int | None = None,
                      lot_stock_id: int | None = None,
                      order_id: int | None = None,
                      date_from: date | None = None,
                      date_to: date | None = None,
                      limit: int = Query(default=100, ge=1, le=movement_service.MAX_MOVEMENTS),
                      session: Session = Depends(get_session),
                      manager: dict = Depends(manager_required)):
    """Retrieve the stock movements, the newest first. Every filter is optional.

    Args (query string):
        the following filters are optional:
        type (str): RESTOCK, DEDUCTION, RETURN or ADJUSTMENT.
        ingredient_id (int): Only the lots of this ingredient.
        lot_stock_id (int): Only this lot.
        order_id (int): Only this client order.
        date_from (date): From this day, included (YYYY-MM-DD).
        date_to (date): Up to this day, included (YYYY-MM-DD).
        limit (int): The most movements returned (1 to 500, default 100).

    Returns:
        A JSON object containing a list of movements and HTTP 200 (OK).
        On error: JSON error message and appropriate HTTP status code
        (403 not a Manager, 422 invalid filter, 500 server error).
    """
    try:
        movements = movement_service.list_movements(
            session, movement_type=type, ingredient_id=ingredient_id, lot_stock_id=lot_stock_id,
            order_id=order_id, date_from=date_from, date_to=date_to, limit=limit
        )
        return JSONResponse({'movements': [movement_json(m) for m in movements]}, status_code=200)
    except Exception as e:
        return error_response(session, e, 'reading the stock movements')
