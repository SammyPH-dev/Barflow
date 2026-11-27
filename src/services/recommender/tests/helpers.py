"""Small test fixtures. They never read the database."""
from datetime import date
from src.services.recommender.schemas import Recipe, Stock

TODAY = date(2026, 11, 27)

class FixedDate(date):
    @classmethod
    def today(cls):
        return TODAY


def stock(ingredient_id=23, quantity="10", expiry=TODAY, unit="g"):
    return Stock(ingredient_id=ingredient_id, name=f"Ingredient {ingredient_id}",
                 mesure_unit=unit, usable_quantity=quantity,
                 reorder_threshold="0", below_threshold=False, next_expiry=expiry)


def recipe(recipe_id=1, requirements=((23, "5", "g"),)):
    return Recipe(recipe_id=recipe_id, name=f"Recipe {recipe_id}", ingredient_ids=[
        {"ingredient_id": key, "quantity": quantity, "unit": unit}
        for key, quantity, unit in requirements
    ])
