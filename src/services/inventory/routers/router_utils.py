"""
Router Utilities Module

This module contains the small helpers shared by every inventory route

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from decimal import Decimal

from fastapi.responses import JSONResponse

from ..services.errors import InvalidOperationError, InventoryError, NotFoundError

QUANTITY_PLACES = Decimal('0.001') # quantities: 3 digits after the dot (ml / g / units)
MONEY_PLACES = Decimal('0.01') # money: 2 digits after the dot


def error_response(session, e, action):
    """Cancel the changes of the request and send back the error with the right status code.

    Args:
        session: The database session of the request.
        e (Exception): The error that was raised.
        action (str): What the route was doing, used in the 500 message.
            ex: 'creating the ingredient'

    Returns:
        A JSONResponse: 404 not found, 409 invalid operation, 400 other inventory error, 500 anything else.
    """

    # SQLAlchemy session
    session.rollback()

    # NotFoundError and InvalidOperationError
    # are special cases of InventoryError, so they are checked first
    if isinstance(e, NotFoundError):
        return JSONResponse({'error': str(e)}, status_code=404)
    if isinstance(e, InvalidOperationError):
        return JSONResponse({'error': str(e)}, status_code=409)
    if isinstance(e, InventoryError):
        return JSONResponse({'error': str(e)}, status_code=400)

    return JSONResponse({
        'error': f'An error occurred while {action}.',
        'details': str(e)
    }, status_code=500)


# decimals are sent as text (ex: "750.000") for easier manipulation and sending as JSON
def quantity_json(value):
    return str(Decimal(value).quantize(QUANTITY_PLACES))


def money_json(value):
    return str(Decimal(value).quantize(MONEY_PLACES))


# dates are sent as text "YYYY-MM-DD", if no value "None"
def date_json(value):
    return value.isoformat() if value is not None else None


def movement_json(movement):
    # one change to the quantity of a lot (see models/stock_movement.py)
    return {
        'id': movement._id,
        'lot_stock_id': movement._lot_stock_id,
        'type': movement._type.value,
        'quantity_change': quantity_json(movement._quantity_change),
        'order_id': movement._order_id,
        'reason': movement._reason,
        'user_id': movement._user_id,
        'created_at': movement._created_at.isoformat()
    }


def alert_json(alert):
    return {
        'ingredient_id': alert['ingredient_id'],
        'name': alert['name'],
        'usable_quantity': quantity_json(alert['usable_quantity']),
        'reorder_threshold': alert['reorder_threshold']
    }
