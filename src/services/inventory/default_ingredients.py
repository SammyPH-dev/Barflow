"""
Default Ingredients Module

This module fills the ingredient table with some pre made ingredients.

Each ingredient has a shelf life (in days).
When a supplier order is passed, the expiry date of its lot is the order day + the shelf life.
No shelf life means the ingredient never expires (ex: a sealed bottle of alcohol).

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""


from sqlalchemy import func, select

from .models import Ingredient, MesureUnit


def default_ingredients_if_db_empty(session):
    """
    Inserts the default ingredients if the ingredient table is currently empty.
    The shelf lives and the reorder thresholds are starting values, they can be updated
    later with PATCH /ingredients/{id}.
    """
    ingredient_count = session.execute(
        select(func.count()).select_from(Ingredient)
    ).scalar()

    if ingredient_count > 0:
        return

    ingredients_data = [

        # name, unit, reorder threshold, shelf life in days (None = never expires)

        # spirits and liqueurs (ml)
        ("Rhum", MesureUnit.ML, 750, None),
        ("Vodka", MesureUnit.ML, 750, None),
        ("Gin", MesureUnit.ML, 750, None),
        ("Whisky", MesureUnit.ML, 750, None),
        ("Tequila", MesureUnit.ML, 750, None),
        ("Triple sec", MesureUnit.ML, 500, None),
        ("Vermouth", MesureUnit.ML, 500, 90),

        # syrups (ml)
        ("Sirop de cerise", MesureUnit.ML, 500, 180),
        ("Sirop d'érable", MesureUnit.ML, 500, 180),
        ("Sirop simple", MesureUnit.ML, 500, 30),

        # juices, dairy and mixers (ml)
        ("Jus de lime", MesureUnit.ML, 500, 3),
        ("Jus de citron", MesureUnit.ML, 500, 3),
        ("Jus de canneberge", MesureUnit.ML, 1000, 14),
        ("Lait", MesureUnit.ML, 1000, 7),
        ("Crème", MesureUnit.ML, 500, 10),
        ("Eau gazeuse", MesureUnit.ML, 2000, 180),
        ("Eau tonique", MesureUnit.ML, 2000, 180),
        ("Ginger beer", MesureUnit.ML, 2000, 120),

        # fresh produce (units) and dry goods (g)
        ("Lime", MesureUnit.UNIT, 10, 14),
        ("Citron", MesureUnit.UNIT, 10, 14),
        ("Orange", MesureUnit.UNIT, 6, 14),
        ("Cerise au marasquin", MesureUnit.UNIT, 20, 365),
        ("Menthe fraîche", MesureUnit.G, 50, 5),
        ("Sucre", MesureUnit.G, 500, None),
        ("Sel", MesureUnit.G, 250, None),
    ]

    for name, mesure_unit, reorder_threshold, shelf_life_days in ingredients_data:
        session.add(Ingredient(
            _name=name,
            _mesure_unit=mesure_unit,
            _reorder_threshold=reorder_threshold,
            _shelf_life_days=shelf_life_days
        ))
