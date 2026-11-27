"""Validate data contracts, conversion, constraints, and JSON shape."""
import unittest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from src.services.recommender.schemas import (
    Stock, Recipe, RecipeIngredient, ExpiringDrink, PopularDrink, Recommendations, StatusResponse,
)
from .helpers import stock, recipe


class SchemaTests(unittest.TestCase):
    def test_stock_converts_dates_and_decimal_strings(self):
        data = stock().model_dump(mode="json")
        result = Stock.model_validate(data)
        self.assertIsInstance(result.next_expiry, date)
        self.assertIsInstance(result.usable_quantity, Decimal)
        self.assertIsInstance(result.reorder_threshold, Decimal)
        self.assertEqual(result.model_dump(mode="json"), data)
        self.assertIsNone(stock(expiry=None).next_expiry)

    def test_stock_rejects_negative_quantities_and_invalid_dates(self):
        for field, value in [("usable_quantity", "-1"), ("reorder_threshold", "-1"), ("next_expiry", "not-a-date")]:
            data = stock().model_dump()
            data[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Stock.model_validate(data)

    def test_recipe_parses_nested_ingredients(self):
        result = Recipe.model_validate(recipe().model_dump(mode="json"))
        self.assertIsInstance(result.ingredient_ids[0], RecipeIngredient)
        self.assertEqual(result.ingredient_ids[0].quantity, Decimal("5"))

    def test_recipe_ingredient_quantity_must_be_positive(self):
        for quantity in ["0", "-1"]:
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                RecipeIngredient(ingredient_id=1, quantity=quantity, unit="ml")

    def test_popularity_count_is_optional_but_nonnegative(self):
        self.assertIsNone(PopularDrink(recipe_id=1, name="Test").quantity_ordered)
        self.assertEqual(PopularDrink(recipe_id=1, name="Test", quantity_ordered=0).quantity_ordered, 0)
        with self.assertRaises(ValidationError):
            PopularDrink(recipe_id=1, name="Test", quantity_ordered=-1)

    def test_expiring_drink_requires_a_reason(self):
        with self.assertRaises(ValidationError):
            ExpiringDrink(recipe_id=1, name="Test")

    def test_recommendation_lists_have_no_double_wrapper(self):
        data = {"expiring_drinks": [{"recipe_id": 1, "name": "Test", "reason": "Tomorrow"}],
                "popular_drinks": [{"recipe_id": 2, "name": "Popular", "quantity_ordered": 3}]}
        result = Recommendations.model_validate(data)
        self.assertIsInstance(result.expiring_drinks[0], ExpiringDrink)
        self.assertIsInstance(result.popular_drinks[0], PopularDrink)
        self.assertEqual(result.model_dump(mode="json"), data)
        self.assertEqual(Recommendations(expiring_drinks=[], popular_drinks=[]).expiring_drinks, [])

    def test_status_requires_message(self):
        self.assertEqual(StatusResponse(message="Ready").model_dump(), {"message": "Ready"})
        with self.assertRaises(ValidationError):
            StatusResponse()
