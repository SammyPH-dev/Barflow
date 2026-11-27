"""In-process endpoint contract tests; service functions are mocked."""
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.exceptions import ResponseValidationError
from src.services.recommender.main import app
from src.services.recommender.schemas import ExpiringDrink, Recommendations
from .helpers import stock

PREFIX = "/api/v1/recommendations"
ROUTER = "src.services.recommender.router"


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_root(self):
        response = self.client.get(PREFIX + "/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "API is online"})

    def test_stock_endpoint_serializes_model(self):
        mocked = AsyncMock(return_value=[stock()])
        with patch(ROUTER + ".get_expiring_stocks", mocked):
            response = self.client.get(PREFIX + "/expiring_stocks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [stock().model_dump(mode="json")])
        mocked.assert_awaited_once_with()

    def test_expiring_recipe_endpoint_returns_reasons(self):
        drink = ExpiringDrink(recipe_id=1, name="Test", reason="Tomorrow")
        mocked = AsyncMock(return_value=[drink])
        with patch(ROUTER + ".get_expiring_recipe_recommendations", mocked):
            response = self.client.get(PREFIX + "/expiring_recipes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [drink.model_dump()])
        mocked.assert_awaited_once_with()

    def test_combined_endpoint(self):
        result = Recommendations(expiring_drinks=[], popular_drinks=[])
        mocked = AsyncMock(return_value=result)
        with patch(ROUTER + ".get_recommendations", mocked):
            response = self.client.get(PREFIX + "/drinks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), result.model_dump())
        mocked.assert_awaited_once_with()

    def test_invalid_service_output_is_rejected(self):
        with patch(ROUTER + ".get_expiring_stocks", AsyncMock(return_value=[{}])):
            with self.assertRaises(ResponseValidationError):
                self.client.get(PREFIX + "/expiring_stocks")

    def test_service_error_is_not_a_successful_empty_response(self):
        with patch(ROUTER + ".get_expiring_stocks", AsyncMock(side_effect=RuntimeError("offline"))):
            with TestClient(app, raise_server_exceptions=False) as client:
                self.assertEqual(client.get(PREFIX + "/expiring_stocks").status_code, 500)

    def test_main_registers_all_documented_routes(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        for suffix in ["/", "/drinks", "/expiring_stocks", "/expiring_recipes"]:
            operation = response.json()["paths"][PREFIX + suffix]["get"]
            self.assertIn("schema", operation["responses"]["200"]["content"]["application/json"])
