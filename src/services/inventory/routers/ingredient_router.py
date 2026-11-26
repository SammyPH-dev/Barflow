"""
Ingredient Routes Module

This module implements the REST endpoints for the ingredients (name, unit, shelf life, reorder threshold).

Permissions:
Reading the ingredients: any logged-in user.
Everything else: Manager only.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database_connection import get_session
from ..permissions import manager_required, user_required
from ..schemas.ingredient import IngredientDbSchema, IngredientUpdateDbSchema
from ..services import ingredient_service
from .router_utils import error_response

router = APIRouter(tags=['ingredients'])


def ingredient_json(ingredient):
    return {
        'id': ingredient._id,
        'name': ingredient._name,
        'mesure_unit': ingredient._mesure_unit.value,
        'reorder_threshold': ingredient._reorder_threshold,
        'shelf_life_days': ingredient._shelf_life_days # null = never expires
    }


# get_all_ingredients()
@router.get('/ingredients')
def get_all_ingredients(session: Session = Depends(get_session),
                        user: dict = Depends(user_required)):
    """Retrieve every ingredient, sorted by name.

    Returns:
        A JSON object containing a list of ingredients (id, name, mesure_unit,
        reorder_threshold, shelf_life_days) and HTTP 200 (OK).
        On error: HTTP 401 (Unauthorized) if the user headers are missing or invalid.
    """
    ingredients = ingredient_service.get_all_ingredients(session)

    return JSONResponse(
        {'ingredients': [ingredient_json(ingredient) for ingredient in ingredients]},
        status_code=200
    )


# create_ingredient()
@router.post('/ingredients')
def create_ingredient(data: IngredientDbSchema,
                      session: Session = Depends(get_session),
                      manager: dict = Depends(manager_required)):
    """Create a new ingredient.

    Args:
        None. The ingredient is obtained from the JSON request body containing:
            - name (str): Name of the ingredient (must be unique).
            - mesure_unit (str): 'ml', 'g' or 'unit'.
            - reorder_threshold (int, optional): Stock quantity under which an alert is sent (0 = no alert).
            - shelf_life_days (int, optional): Days the ingredient lasts after it is ordered,
              absent = never expires.

    Returns:
        A JSON object containing the created ingredient and HTTP 201 (Created).
        On error: JSON error message and appropriate HTTP status code
        (403 not a Manager, 409 name already used, 422 invalid data, 500 server error).
    """
    try:
        ingredient = ingredient_service.create_ingredient(session, data)
        session.commit()

        return JSONResponse(ingredient_json(ingredient), status_code=201)
    except Exception as e:
        return error_response(session, e, 'creating the ingredient')


# update_ingredient(ingredient_id)
@router.patch('/ingredients/{ingredient_id}')
def update_ingredient(ingredient_id: int,
                      data: IngredientUpdateDbSchema,
                      session: Session = Depends(get_session),
                      manager: dict = Depends(manager_required)):
    """Update an ingredient. Only the fields sent are changed.

    Args:
        ingredient_id (int): The id of the ingredient to update.

    Returns:
        A JSON object containing the updated ingredient and HTTP 200 (OK).
        On error: JSON error message and appropriate HTTP status code
        (400 no data, 403 not a Manager, 404 unknown ingredient,
        409 name already used or null field, 422 invalid data, 500 server error).
    """
    try:
        ingredient = ingredient_service.update_ingredient(session, ingredient_id, data)
        session.commit()

        return JSONResponse(ingredient_json(ingredient), status_code=200)
    except Exception as e:
        return error_response(session, e, f'updating the ingredient with id "{ingredient_id}"')
