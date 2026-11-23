"""
Ingredient Service Module

This module contains the business logic of the ingredients:
listing, creating and updating ingredients.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from sqlalchemy import select

from ..models import Ingredient
from .errors import InvalidOperationError, InventoryError, NotFoundError


def get_all_ingredients(session):
    # Return every ingredient, sorted by name
    return list(session.scalars(select(Ingredient).order_by(Ingredient._name)))


def create_ingredient(session, data):
    """Creates a new ingredient. The name must be unique.

    Args:
        session: The database session of the request.
        data (IngredientDbSchema): The validated ingredient data.

    Returns:
        The new Ingredient.

    Raises:
        InvalidOperationError: If an ingredient with this name already exists.
    """
    if name_is_taken(session, data.name):
        raise InvalidOperationError(f'An ingredient named "{data.name}" already exists.')

    ingredient = Ingredient(
        _name=data.name,
        _mesure_unit=data.mesure_unit,
        _reorder_threshold=data.reorder_threshold,
        _shelf_life_days=data.shelf_life_days
    )
    session.add(ingredient)

    return ingredient


def update_ingredient(session, ingredient_id, data):
    """Changes only the fields of the ingredient that were sent by the client.

    Args:
        session: The database session of the request.
        ingredient_id (int): The id of the ingredient to update.
        data (IngredientUpdateDbSchema): The validated fields to change.

    Returns:
        The updated Ingredient.

    Raises:
        NotFoundError: If the ingredient does not exist.
        InventoryError: If no field was sent.
        InvalidOperationError: If a field is null or the new name is already used.
    """
    ingredient = session.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise NotFoundError(f'Ingredient with id "{ingredient_id}" not found.')

    # exclude_unset=True: only the fields sent by the client are put in the dict
    # all other fields stay untouched instead of defaulting to "None"
    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise InventoryError('No data provided to update.')

    # template for the expected json fields and the matching model attributes
    updatable_fields = {
        'name': '_name',
        'mesure_unit': '_mesure_unit',
        'reorder_threshold': '_reorder_threshold',
        'shelf_life_days': '_shelf_life_days'
    }

    # a null field is not allowed here, except for shelf_life_days where it means "no expiration date"
    for field in ('name', 'mesure_unit', 'reorder_threshold'):
        if field in changes and changes[field] is None:
            raise InvalidOperationError(f'The field "{field}" cannot be null.')

    if 'name' in changes and name_is_taken(session, changes['name'], ingredient_id):
        raise InvalidOperationError(f'An ingredient named "{changes["name"]}" already exists.')

    for field, attribute in updatable_fields.items():
        # if field in template corresponds to field in changes,
        # ingredient._attribute_x = changes[field_x]
        if field in changes:
            setattr(ingredient, attribute, changes[field])

    return ingredient


def name_is_taken(session, name, exclude_id=None):
    """
    True if another ingredient already uses this name.
    exclude_id lets an ingredient keep its own name when it is updated.
    """
    query = select(Ingredient._id).where(Ingredient._name == name)
    if exclude_id is not None:
        query = query.where(Ingredient._id != exclude_id)

    return session.execute(query.limit(1)).first() is not None
