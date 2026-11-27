"""Exercise real HTTPX parsing with an in-memory transport, never a server."""
import unittest
from unittest.mock import patch
import httpx
from pydantic import ValidationError
from src.services.recommender import inventory_client
from .helpers import stock


class InventoryClientTests(unittest.IsolatedAsyncioTestCase):
    async def request_with(self, handler):
        # Preserve the real class before patching the client's constructor.
        real_client = httpx.AsyncClient
        with patch.object(inventory_client.httpx, "AsyncClient", side_effect=lambda **kwargs:
                          real_client(transport=httpx.MockTransport(handler), **kwargs)):
            return await inventory_client.get_inventory_stock("http://inventory.test", 7, "EMPLOYEE")

    async def test_request_path_headers_and_stock_conversion(self):
        def handler(request):
            self.assertEqual(request.method, "GET")
            self.assertEqual(str(request.url), "http://inventory.test/api/v1/inventory/stock")
            self.assertEqual(request.headers["X-User-Id"], "7")
            self.assertEqual(request.headers["X-User-Role"], "EMPLOYEE")
            return httpx.Response(200, json={"stock": [stock().model_dump(mode="json")]})
        self.assertEqual(await self.request_with(handler), [stock()])

    async def test_empty_inventory(self):
        self.assertEqual(await self.request_with(lambda request: httpx.Response(200, json={"stock": []})), [])

    async def test_http_errors_are_propagated(self):
        for status in [401, 403, 500]:
            with self.subTest(status=status), self.assertRaises(httpx.HTTPStatusError):
                await self.request_with(lambda request: httpx.Response(status, json={"detail": "failure"}))

    async def test_connection_and_timeout_errors_are_propagated(self):
        for error in [httpx.ConnectError, httpx.ReadTimeout]:
            def handler(request):
                raise error("unavailable", request=request)
            with self.subTest(error=error), self.assertRaises(error):
                await self.request_with(handler)

    async def test_malformed_stock_is_rejected(self):
        with self.assertRaises(ValidationError):
            await self.request_with(lambda request: httpx.Response(200, json={"stock": [{"ingredient_id": 1}]}))

    async def test_missing_stock_key_is_not_an_empty_inventory(self):
        with self.assertRaises(KeyError):
            await self.request_with(lambda request: httpx.Response(200, json={}))
