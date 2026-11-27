"""
Stock Routes Module

This module implements the REST endpoints that read the stock levels and the reorder alerts.
Its endpoints are the ones the order service calls when an item is added (+) or removed (-) on a client order.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database_connection import get_session
from ..permissions import manager_required, user_required
from ..schemas.stock_update import DeductionDbSchema, ReturnDbSchema
from ..services import client_order_service, stock_service
from .router_utils import alert_json, date_json, error_response, quantity_json

router = APIRouter(tags=['stock'])


def stock_level_json(level):
    # usable stock of one ingredient (lots with quantity > 0 that are not expired)
    return {
        'ingredient_id': level['ingredient_id'],
        'name': level['name'],
        'mesure_unit': level['mesure_unit'],
        'usable_quantity': quantity_json(level['usable_quantity']),
        'reorder_threshold': level['reorder_threshold'],
        'below_threshold': level['below_threshold'],
        'next_expiry': date_json(level['next_expiry'])
    }


# get_all_stock()
@router.get('/stock')
def get_all_stock(session: Session = Depends(get_session),
                user: dict = Depends(user_required)):
    """Retrieve the usable stock of every ingredient.

    Any logged-in user. The recommendation service reads it too.

    Returns:
        A JSON object containing a list of stock levels and HTTP 200 (OK).
        On error: HTTP 401 (Unauthorized) if the user headers are missing or invalid.
    """
    levels = stock_service.get_all_stock_levels(session)

    return JSONResponse({'stock': [stock_level_json(level) for level in levels]}, status_code=200)


# get_stock(ingredient_id)
@router.get('/stock/{ingredient_id}')
def get_stock(ingredient_id: int,
            session: Session = Depends(get_session),
            user: dict = Depends(user_required)):
    """Retrieve the usable stock of one ingredient.

    Args:
        ingredient_id (int): The id of the ingredient.

    Returns:
        A JSON object containing the stock level and HTTP 200 (OK).
        On error: HTTP 404 (Not Found) if the ingredient does not exist.
    """
    try:
        level = stock_service.get_stock_level(session, ingredient_id)
        return JSONResponse(stock_level_json(level), status_code=200)
    except Exception as e:
        return error_response(session, e, f'reading the stock of the ingredient with id "{ingredient_id}"')


# get_all_alerts()
@router.get('/alerts')
def get_all_alerts(session: Session = Depends(get_session),
                manager: dict = Depends(manager_required)):
    """Retrieve every ingredient whose usable stock is below its reorder threshold.

    Manager only.

    Returns:
        A JSON object containing a list of alerts and HTTP 200 (OK).
        On error: HTTP 401 (Unauthorized) or HTTP 403 (Forbidden) if the user is not a Manager.
    """
    alerts = stock_service.get_all_alerts(session)

    return JSONResponse({'alerts': [alert_json(alert) for alert in alerts]}, status_code=200)


# the next 2 functions are called by the order service when + or - is pressed on the POS,
# through the API Gateway with the user's identity it received passed on

# deduct_stock()
@router.post('/deductions')
def deduct_stock(data: DeductionDbSchema,
                session: Session = Depends(get_session),
                user: dict = Depends(user_required)):
    """Deduct the ingredients of an item added to a client order (+ on the POS),
    all ingredients from that item (recipe) or nothing.

    Args:
        None. The deduction is obtained from the JSON request body containing:
            - order_id (int): The id of the client order in the order service.
            - button_press_id (str): Unique id of this + press (offline POS can resend it).
            - items (list): Each ingredient_id (int) of the item's recipe with its quantity
            (decimal, liquids in ml).

    Returns:
        A JSON object (order_id, success, shortages, alerts) and HTTP 200 (OK).
        A shortage is NOT an error: success is false, nothing was deducted,
        the item is not added and the POS shows the "not enough stock" warning.
        On error: JSON error message and appropriate HTTP status code
        (404 unknown ingredient, 422 invalid data, 500 server error).
    """
    try:
        result = client_order_service.deduct(session, data, user_id=user['id'])
        session.commit()

        return JSONResponse({
            'order_id': result['order_id'],
            'success': result['success'],
            'shortages': [
                {
                    'ingredient_id': shortage['ingredient_id'],
                    'requested': quantity_json(shortage['requested']),
                    'available': quantity_json(shortage['available'])
                }
                for shortage in result['shortages']
            ],
            # thresholds crossed by this deduction
            'alerts': [alert_json(alert) for alert in result['alerts']]
        }, status_code=200)
    except Exception as e:
        return error_response(session, e, f'deducting the stock of the order with id "{data.order_id}"')


# return_stock()
@router.post('/returns')
def return_stock(data: ReturnDbSchema,
                session: Session = Depends(get_session),
                user: dict = Depends(user_required)):
    """Give back the ingredients of an item removed from a client order (- on the POS).

    The quantities go back to the same lots they were taken from.
    Sending the same button press id again is safe.
    This is important because if 30ml were taken from lot1 and 25ml from lot2,
    when returning them to the inventory (- on POS), the exact amounts need to be returned to the proper lots,
    this way they keep their same expiry date

    Args:
        None. The return is obtained from the JSON request body containing:
            - order_id (int): The id of the client order in the order service.
            - button_press_id (str): Unique id of this - press (offline POS can resend it).
            - items (list): Each ingredient_id (int) of the item's recipe with its quantity.

    Returns:
        A JSON success message and HTTP 200 (OK).
        On error: JSON error message and appropriate HTTP status code
        (404 unknown ingredient, 409 more than the order took, 422 invalid data, 500 server error).
    """
    try:
        client_order_service.return_items(session, data, user_id=user['id'])
        session.commit()

        return JSONResponse(
            {'message': f'Item of the order with id "{data.order_id}" returned to the inventory successfully !'},
            status_code=200
        )
    except Exception as e:
        return error_response(session, e, f'returning an item of the order with id "{data.order_id}"')
