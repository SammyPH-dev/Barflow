"""Popularity rules and shared inventory tests; all external inputs are mocked."""
import unittest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from src.services.recommender import service
from src.services.recommender.schemas import RecipeSalesCount
from .helpers import recipe, stock, FixedDate


def sales(recipe_id, quantity):
    return RecipeSalesCount(recipe_id=recipe_id, quantity_ordered=quantity)


class PopularityTests(unittest.IsolatedAsyncioTestCase):
    async def test_lookup_uses_recipe_ids_and_does_not_duplicate_results(self):
        samples = [recipe(1), recipe(2)]
        with patch.object(service, "sample_recipes", [r.model_dump() for r in samples]):
            self.assertEqual(await service.get_recipes_by_ids([2, 2, 99]), [samples[1]])
            self.assertEqual(await service.get_recipes_by_ids([]), [])

    async def test_sample_sales_return_valid_unique_recipe_totals(self):
        results = await service.get_recipe_sales_counts()
        self.assertTrue(results)
        self.assertTrue(all(isinstance(row, RecipeSalesCount) for row in results))
        self.assertTrue(all(row.quantity_ordered >= 0 for row in results))
        self.assertEqual(len({row.recipe_id for row in results}), len(results))

    async def test_ranking_excludes_unavailable_zero_sales_and_unknown_recipes(self):
        samples = [recipe(1), recipe(2), recipe(3, ((99, "5", "g"),)), recipe(4)]
        counts = [sales(1, 28), sales(2, 45), sales(3, 100), sales(4, 0), sales(999, 200)]
        inventory = AsyncMock(side_effect=AssertionError("Unexpected inventory fetch"))
        with patch.object(service, "sample_recipes", [r.model_dump() for r in samples]), patch.object(
            service, "get_recipe_sales_counts", AsyncMock(return_value=counts)
        ), patch.object(service, "get_inventory_stock", inventory):
            result = await service.get_popular_drink_recommendations([stock()])
        self.assertEqual([(r.recipe_id, r.quantity_ordered) for r in result], [(2, 45), (1, 28)])
        self.assertEqual(result[0].name, samples[1].name)
        inventory.assert_not_awaited()

    async def test_top_ten_is_applied_after_availability_filter(self):
        samples = [recipe(i) for i in range(1, 13)]
        samples.append(recipe(99, ((99, "5", "g"),)))
        counts = [sales(i, i) for i in range(1, 13)] + [sales(99, 1000)]
        with patch.object(service, "sample_recipes", [r.model_dump() for r in samples]), patch.object(
            service, "get_recipe_sales_counts", AsyncMock(return_value=counts)
        ):
            result = await service.get_popular_drink_recommendations([stock()])
        self.assertEqual([r.recipe_id for r in result], list(range(12, 2, -1)))

    async def test_ties_keep_recipe_order(self):
        samples = [recipe(2), recipe(1)]
        with patch.object(service, "sample_recipes", [r.model_dump() for r in samples]), patch.object(
            service, "get_recipe_sales_counts", AsyncMock(return_value=[sales(1, 5), sales(2, 5)])
        ):
            result = await service.get_popular_drink_recommendations([stock()])
        self.assertEqual([r.recipe_id for r in result], [2, 1])

    async def test_no_sales_returns_empty(self):
        with patch.object(service, "get_recipe_sales_counts", AsyncMock(return_value=[])):
            self.assertEqual(await service.get_popular_drink_recommendations([stock()]), [])

    async def test_popularity_fetches_inventory_when_omitted(self):
        inventory = AsyncMock(return_value=[stock()])
        with patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "sample_recipes", [recipe().model_dump()]
        ), patch.object(service, "get_recipe_sales_counts", AsyncMock(return_value=[sales(1, 3)])):
            result = await service.get_popular_drink_recommendations()
        self.assertEqual([r.recipe_id for r in result], [1])
        inventory.assert_awaited_once()

    async def test_explicit_empty_inventory_is_never_refetched(self):
        inventory = AsyncMock(side_effect=AssertionError("Empty is not missing"))
        with patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "get_recipe_sales_counts", AsyncMock(return_value=[sales(1, 3)])
        ):
            self.assertEqual(await service.get_popular_drink_recommendations([]), [])
            self.assertEqual(await service.get_expiring_recipe_recommendations([]), [])
        inventory.assert_not_awaited()

    async def test_supplied_inventory_is_used_by_expiry_calculation(self):
        inventory = AsyncMock(side_effect=AssertionError("Unexpected fetch"))
        with patch.object(service, "date", FixedDate), patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "sample_recipes", [recipe().model_dump()]
        ):
            result = await service.get_expiring_recipe_recommendations([stock()])
        self.assertEqual([r.recipe_id for r in result], [1])
        inventory.assert_not_awaited()

    async def test_combined_real_calculations_fetch_inventory_once(self):
        inventory = AsyncMock(return_value=[stock()])
        with patch.object(service, "date", FixedDate), patch.object(service, "get_inventory_stock", inventory), patch.object(
            service, "sample_recipes", [recipe().model_dump()]
        ), patch.object(service, "get_recipe_sales_counts", AsyncMock(return_value=[sales(1, 3)])):
            result = await service.get_recommendations()
        self.assertEqual([r.recipe_id for r in result.expiring_drinks], [1])
        self.assertEqual([r.recipe_id for r in result.popular_drinks], [1])
        inventory.assert_awaited_once()

    async def test_sales_failure_is_not_silently_reported_as_empty(self):
        with patch.object(service, "get_recipe_sales_counts", AsyncMock(side_effect=RuntimeError("sales offline"))):
            with self.assertRaisesRegex(RuntimeError, "sales offline"):
                await service.get_popular_drink_recommendations([stock()])

    def test_sales_schema_requires_nonnegative_quantity(self):
        self.assertEqual(sales(1, 0).quantity_ordered, 0)
        with self.assertRaises(ValidationError):
            sales(1, -1)
        with self.assertRaises(ValidationError):
            RecipeSalesCount(recipe_id=1)
