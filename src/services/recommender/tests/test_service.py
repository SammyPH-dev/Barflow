"""Business-rule tests with a fixed date and mocked inventory requests."""
import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from src.services.recommender import service
from src.services.recommender.schemas import ExpiringDrink, Recipe, Recommendations
from .helpers import TODAY, FixedDate, recipe, stock


class RuleTests(unittest.TestCase):
    def setUp(self):
        # Patch only the date used by this service; no machine clock changes.
        date_patch = patch.object(service, "date", FixedDate)
        date_patch.start()
        self.addCleanup(date_patch.stop)

    def test_expiry_window_includes_today_and_day_seven_only(self):
        rows = [stock(i, expiry=TODAY + timedelta(days=days))
                for i, days in enumerate((-1, 0, 1, 7, 8))]
        result = service._filter_expiring_stocks(rows, 7)
        self.assertEqual([s.ingredient_id for s in result], [1, 2, 3])

    def test_expiry_filter_skips_zero_stock_and_missing_dates(self):
        self.assertEqual(service._filter_expiring_stocks(
            [stock(quantity="0"), stock(expiry=None)], 7), [])
        self.assertEqual(service._filter_expiring_stocks([], 7), [])

    def test_zero_day_window_selects_today_only(self):
        self.assertEqual(service._filter_expiring_stocks(
            [stock(), stock(2, expiry=TODAY + timedelta(days=1))], 0), [stock()])

    def test_availability_quantity_boundaries(self):
        for quantity, expected in [("4.999", False), ("5", True), ("5.001", True)]:
            with self.subTest(quantity=quantity):
                self.assertEqual(service._has_enough_stock(recipe(), [stock(quantity=quantity)]), expected)

    def test_availability_rejects_missing_ingredient_wrong_unit_and_empty_recipe(self):
        for candidate, rows in [(recipe(), []), (recipe(), [stock(99)]),
                                (recipe(), [stock(unit="ml")]), (recipe(requirements=()), [stock()])]:
            with self.subTest(candidate=candidate, rows=rows):
                self.assertFalse(service._has_enough_stock(candidate, rows))

    def test_availability_checks_every_ingredient_in_any_stock_order(self):
        candidate = recipe(requirements=((23, "5", "g"), (1, "50", "ml")))
        self.assertFalse(service._has_enough_stock(candidate, [stock(), stock(1, "49", unit="ml")]))
        self.assertTrue(service._has_enough_stock(candidate, [stock(1, "50", expiry=None, unit="ml"), stock()]))

    def test_available_recipe_filter_preserves_order_and_does_not_deduct_stock(self):
        candidates = [recipe(1), recipe(2, ((99, "5", "g"),)), recipe(3)]
        rows = [stock()]
        before = rows[0].model_dump()
        result = service.get_available_expiring_recipes(candidates, rows)
        self.assertEqual([r.recipe_id for r in result], [1, 3])
        self.assertEqual(rows[0].model_dump(), before)
        self.assertEqual(service.get_available_expiring_recipes([], rows), [])

    def test_recipe_expiry_ignores_unrelated_and_undated_stock(self):
        candidate = recipe(requirements=((23, "5", "g"), (1, "1", "ml"), (2, "1", "ml")))
        earliest = TODAY + timedelta(days=2)
        rows = [stock(99, expiry=TODAY), stock(23, expiry=TODAY + timedelta(days=5)),
                stock(1, expiry=None, unit="ml"), stock(2, expiry=earliest, unit="ml")]
        self.assertEqual(service._get_recipe_expiry(candidate, rows), earliest)
        self.assertIsNone(service._get_recipe_expiry(recipe(), [stock(expiry=None)]))
        self.assertIsNone(service._get_recipe_expiry(recipe(), []))

    def test_recommendation_reason_today_tomorrow_and_multiple_days(self):
        for days, ending in [(0, "today."), (1, "tomorrow."), (3, "in 3 days.")]:
            with self.subTest(days=days):
                result = service._build_expiring_drink(recipe(), [stock(expiry=TODAY + timedelta(days=days))])
                self.assertIsInstance(result, ExpiringDrink)
                self.assertEqual(result.recipe_id, 1)
                self.assertEqual(result.name, "Recipe 1")
                self.assertEqual(result.reason, "One of the ingredients is expiring " + ending)

    def test_build_recommendation_requires_a_known_expiry(self):
        with self.assertRaises(ValueError):
            service._build_expiring_drink(recipe(), [stock(expiry=None)])


class ServiceFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        date_patch = patch.object(service, "date", FixedDate)
        date_patch.start()
        self.addCleanup(date_patch.stop)

    async def test_recipe_lookup_matches_any_id_without_duplicates(self):
        samples = [recipe(1, ((23, "5", "g"), (11, "5", "ml"))), recipe(2, ((99, "1", "g"),))]
        with patch.object(service, "sample_recipes", [r.model_dump() for r in samples]):
            result = await service.get_recipes_containing([23, 11, 23])
            self.assertEqual(result, [samples[0]])
            self.assertIsInstance(result[0], Recipe)
            self.assertEqual(await service.get_recipes_containing([]), [])
            self.assertEqual(await service.get_recipes_containing([100]), [])

    async def test_expiring_stock_fetch_is_awaited_and_filtered(self):
        inventory = AsyncMock(return_value=[stock(), stock(2, expiry=None)])
        with patch.object(service, "get_inventory_stock", inventory):
            self.assertEqual(await service.get_expiring_stocks(), [stock()])
        inventory.assert_awaited_once()

    async def test_full_expiry_flow_filters_availability_and_sorts(self):
        # One later recipe, two tied urgent recipes, one missing ingredient,
        # and one recipe with no expiring ingredients.
        samples = [recipe(1), recipe(2, ((11, "5", "g"),)),
                   recipe(3, ((11, "5", "g"),)),
                   recipe(4, ((11, "5", "g"), (99, "1", "g"))),
                   recipe(5, ((1, "50", "ml"),))]
        rows = [stock(expiry=TODAY + timedelta(days=5)),
                stock(11, expiry=TODAY + timedelta(days=1)),
                stock(1, "100", expiry=None, unit="ml")]
        inventory = AsyncMock(return_value=rows)
        with patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "sample_recipes", [r.model_dump() for r in samples]
        ):
            result = await service.get_expiring_recipe_recommendations()
        self.assertEqual([r.recipe_id for r in result], [2, 3, 1])
        self.assertIn("tomorrow", result[0].reason)
        self.assertIn("5 days", result[-1].reason)
        inventory.assert_awaited_once()

    async def test_full_flow_uses_non_expiring_stock_for_availability(self):
        sample = recipe(requirements=((23, "5", "g"), (1, "50", "ml")))
        with patch.object(service, "sample_recipes", [sample.model_dump()]), patch.object(
            service, "get_inventory_stock", AsyncMock(return_value=[stock(), stock(1, "50", expiry=None, unit="ml")])
        ):
            self.assertEqual(len(await service.get_expiring_recipe_recommendations()), 1)

    async def test_empty_inventory_returns_empty_recommendations(self):
        with patch.object(service, "get_inventory_stock", AsyncMock(return_value=[])):
            self.assertEqual(await service.get_expiring_recipe_recommendations(), [])

    async def test_inventory_failure_is_not_silently_treated_as_empty(self):
        with patch.object(service, "get_inventory_stock", AsyncMock(side_effect=RuntimeError("offline"))):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                await service.get_expiring_recipe_recommendations()

    async def test_combined_response_shares_one_inventory_fetch(self):
        from src.services.recommender.schemas import PopularDrink
        rows = [stock()]
        drinks = [ExpiringDrink(recipe_id=9, name="Test", reason="Tomorrow")]
        popular = [PopularDrink(recipe_id=9, name="Test", quantity_ordered=5)]
        inventory = AsyncMock(return_value=rows)
        expiry_lookup = AsyncMock(return_value=drinks)
        popular_lookup = AsyncMock(return_value=popular)
        with patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "get_expiring_recipe_recommendations", expiry_lookup
        ), patch.object(service, "get_popular_drink_recommendations", popular_lookup):
            result = await service.get_recommendations()
        self.assertIsInstance(result, Recommendations)
        self.assertEqual(result.expiring_drinks, drinks)
        self.assertEqual(result.popular_drinks, popular)
        inventory.assert_awaited_once()
        expiry_lookup.assert_awaited_once_with(rows)
        popular_lookup.assert_awaited_once_with(rows)
        self.assertIs(expiry_lookup.await_args.args[0], rows)
        self.assertIs(popular_lookup.await_args.args[0], rows)
