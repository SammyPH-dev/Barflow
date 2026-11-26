"""
Restock Routes Module

This module implements the REST endpoints for the supplier orders (orders to refill the inventory).
For now, a supplier order is received immediately when it is placed.
Manager only.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database_connection import get_session
from ..permissions import manager_required
from ..schemas.supplier_order import SupplierOrderDbSchema
from ..services import supplier_order_service
from .router_utils import date_json, error_response, money_json, quantity_json

router = APIRouter(tags=['restock'])


def lines_json(order):
    # each line of the order, with the lot it created (one lot per line)
    return [
        {
            'id': line._id,
            'ingredient_id': line._ingredient_id,
            'lot_stock_id': line._lot_stock_id,
            'quantity': quantity_json(line._quantity),
            'unit_price': money_json(line._unit_price)
        }
        for line in order._lines
    ]


def supplier_order_json(order):
    return {
        'id': order._id,
        'placed_by': order._placed_by,
        'order_date': order._order_date.isoformat(),
        'status': order._status.value,
        'total': money_json(order._total),
        'lines': lines_json(order)
    }


# create_supplier_order()
@router.post('/supplier-orders')
def create_supplier_order(data: SupplierOrderDbSchema,
                          session: Session = Depends(get_session),
                          manager: dict = Depends(manager_required)):
    """Place a supplier order. It is received immediately: one lot is added to the inventory
    for each line, so the stock goes up right away.

    The expiry date of each lot is calculated from the shelf life of its ingredient
    (ex: an ingredient that lasts 7 days expires 7 days after the order day).

    Args:
        None. The order is obtained from the JSON request body containing:
            - lines (list, at least one, no maximum): Each ingredient_id (int),
              quantity (decimal) and unit_price (decimal).
        The Manager placing the order is taken from the request, not from the body.

    Returns:
        A JSON object containing the created order (status RECEIVED) with its lines
        and the lot of each line, and HTTP 201 (Created).
        On error: nothing is saved and a JSON error message with the appropriate HTTP status code
        (403 not a Manager, 404 unknown ingredient, 422 invalid data, 500 server error).
    """
    try:
        order = supplier_order_service.create_order(session, data, manager_id=manager['id'])
        session.commit()

        return JSONResponse(supplier_order_json(order), status_code=201)
    except Exception as e:
        return error_response(session, e, 'creating the supplier order')


# not sure if this one is needed. Note to self: ask teammates
# get_all_supplier_orders()
@router.get('/supplier-orders')
def get_all_supplier_orders(session: Session = Depends(get_session),
                            manager: dict = Depends(manager_required)):
    """Retrieve every supplier order with its lines, newest first.

    Returns:
        A JSON object containing a list of supplier orders and HTTP 200 (OK).
        On error: HTTP 401 (Unauthorized) or HTTP 403 (Forbidden) if the user is not a Manager.
    """
    orders = supplier_order_service.get_all_orders(session)

    return JSONResponse({'supplier_orders': [supplier_order_json(order) for order in orders]}, status_code=200)


# not sure if this one is needed. Note to self: ask teammates
# get_supplier_order(order_id)
@router.get('/supplier-orders/{order_id}')
def get_supplier_order(order_id: int,
                       session: Session = Depends(get_session),
                       manager: dict = Depends(manager_required)):
    """Retrieve one supplier order with its lines.

    Args:
        order_id (int): The id of the supplier order.

    Returns:
        A JSON object containing the order and HTTP 200 (OK).
        On error: HTTP 403 (Forbidden) if not a Manager, HTTP 404 (Not Found) if unknown.
    """
    try:
        order = supplier_order_service.get_order(session, order_id)
        return JSONResponse(supplier_order_json(order), status_code=200)
    except Exception as e:
        return error_response(session, e, f'reading the supplier order with id "{order_id}"')
