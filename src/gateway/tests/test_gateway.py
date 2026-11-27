"""
API Gateway Tests Module

This module tests the gateway with fake services (httpx MockTransport): no service and no
database need to run. Run it from the src folder:
    python -m unittest discover -s gateway/tests -t .

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import jwt
from fastapi.testclient import TestClient
from services.login.repository import mock_database
from services.login.security import create_access_token

SECRET = 'a-test-secret-that-is-at-least-32-characters-long'
from gateway import config, main  # noqa: E402

# The gateway refuses to start without the secret (normally in local_settings.py, not in Git).
config.JWT_SECRET_KEY = SECRET


def make_token(sub='7', role='Manager', minutes=30, secret=SECRET, **extra):
    """Build a token like the login service does (HS256, sub = user id, role, exp)."""
    payload = {'sub': sub, 'role': role, 'exp': datetime.now(timezone.utc) + timedelta(minutes=minutes), **extra}
    return jwt.encode(payload, secret, algorithm='HS256')


def bearer(token):
    return {'Authorization': f'Bearer {token}'}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.calls = []  # every request that reached a fake service
        self.reply = lambda request: httpx.Response(200, json={'ok': True})

        def fake_services(request):
            self.calls.append(request)
            return self.reply(request)

        # the gateway's HTTP client sends everything to the fake services
        self.original_create_client = main.create_client
        main.create_client = lambda: httpx.AsyncClient(transport=httpx.MockTransport(fake_services))
        self.client = TestClient(main.app)
        self.client.__enter__()  # runs the start up of the gateway

    def tearDown(self):
        self.client.__exit__(None, None, None)
        main.create_client = self.original_create_client
        config.JWT_SECRET_KEY = SECRET

    # ---- routing ----

    def test_each_service_uses_its_configured_url(self):
        for service, base_url in config.SERVICES.items():
            self.client.get(f'/api/v1/{service}/something', headers=bearer(make_token()))
            self.assertEqual(str(self.calls[-1].url), f'{base_url}/api/v1/{service}/something')

    def test_unknown_service(self):
        response = self.client.get('/api/v1/nothing/here', headers=bearer(make_token()))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'Unknown route.'})
        self.assertEqual(self.calls, [])

    # ---- token ----

    def test_missing_token(self):
        response = self.client.get('/api/v1/inventory/stock')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'detail': 'Bearer token required.'})
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')
        self.assertEqual(self.calls, [])

    def test_refused_tokens(self):
        refused = {
            'wrong secret': bearer(make_token(secret='another-secret-that-is-also-32-characters-long')),
            'expired': bearer(make_token(minutes=-1)),
            'not a bearer token': {'Authorization': 'Basic abc'},
            'garbage': bearer('not.a.token'),
            'user id not a number': bearer(make_token(sub='someone@barflow.ca')),
            'unknown role': bearer(make_token(role='chef')),
            'no role': bearer(jwt.encode(
                {'sub': '7', 'exp': datetime.now(timezone.utc) + timedelta(minutes=5)}, SECRET, algorithm='HS256')),
        }
        for case, headers in refused.items():
            with self.subTest(case):
                response = self.client.get('/api/v1/inventory/stock', headers=headers)
                self.assertEqual(response.status_code, 401)
                self.assertIn('detail', response.json())
        self.assertEqual(self.calls, [])

    def test_user_headers_come_from_the_token_only(self):
        # the client tries to pass itself off as a manager: the token says employee
        headers = {**bearer(make_token(sub='7', role='Employee')), 'X-User-Id': '1', 'X-User-Role': 'manager'}
        self.client.get('/api/v1/inventory/alerts', headers=headers)
        sent = self.calls[0].headers
        self.assertEqual(sent['x-user-id'], '7')
        self.assertEqual(sent['x-user-role'], 'employee')

    def test_login_token_is_accepted_by_gateway(self):
        user = mock_database.get_by_email('sammy@barflow.com')
        with patch.dict('os.environ', {'JWT_SECRET_KEY': SECRET}):
            token = create_access_token(user)

        response = self.client.get('/api/v1/inventory/stock', headers=bearer(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls[0].headers['x-user-id'], str(user.user_id))
        self.assertEqual(self.calls[0].headers['x-user-role'], 'manager')

    def test_role_is_lowercase(self):
        for role in ('Manager', 'MANAGER', 'manager'):
            self.client.get('/api/v1/inventory/stock', headers=bearer(make_token(role=role)))
            self.assertEqual(self.calls[-1].headers['x-user-role'], 'manager')

    # ---- public routes ----

    def test_login_needs_no_token(self):
        self.reply = lambda request: httpx.Response(200, json={'access_token': 'abc', 'user_id': 7})
        response = self.client.post('/api/v1/login', json={'email': 'a@b.ca', 'password': 'x'},
                                    headers={'X-User-Role': 'manager'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'access_token': 'abc', 'user_id': 7})
        sent = self.calls[0]
        self.assertEqual(str(sent.url), f"{config.SERVICES['login']}/api/v1/login")
        self.assertNotIn('x-user-id', sent.headers)
        self.assertNotIn('x-user-role', sent.headers)

    def test_recent_users_needs_no_token(self):
        response = self.client.get('/api/v1/login/recent-users')
        self.assertEqual(response.status_code, 200)

    def test_other_login_routes_need_a_token(self):
        response = self.client.get('/api/v1/login/me')
        self.assertEqual(response.status_code, 401)

    # ---- forwarding ----

    def test_request_and_answer_pass_unchanged(self):
        self.reply = lambda request: httpx.Response(409, json={'detail': 'The lot would become negative.'})
        body = {'lot_stock_id': 1, 'quantity_change': '-5.000', 'reason': 'Broken bottle'}
        token = make_token()
        response = self.client.post('/api/v1/inventory/adjustments?dry=1&dry=2', json=body, headers=bearer(token))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {'detail': 'The lot would become negative.'})
        sent = self.calls[0]
        self.assertEqual(sent.method, 'POST')
        self.assertEqual(
            str(sent.url),
            f"{config.SERVICES['inventory']}/api/v1/inventory/adjustments?dry=1&dry=2",
        )
        self.assertEqual(json.loads(sent.content), body)
        self.assertEqual(sent.headers['content-type'], 'application/json')
        self.assertEqual(sent.headers['authorization'], f'Bearer {token}')

    def test_other_client_headers_are_not_forwarded(self):
        self.client.get('/api/v1/inventory/stock', headers={**bearer(make_token()), 'X-Something': 'x'})
        self.assertNotIn('x-something', self.calls[0].headers)

    def test_every_method_is_forwarded(self):
        for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            self.client.request(method, '/api/v1/inventory/ingredients/1', headers=bearer(make_token()))
            self.assertEqual(self.calls[-1].method, method)

    # ---- service problems ----

    def test_service_down(self):
        def refused(request):
            raise httpx.ConnectError('Connection refused', request=request)
        self.reply = refused
        response = self.client.get('/api/v1/inventory/stock', headers=bearer(make_token()))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'detail': 'The inventory service is unavailable.'})

    # ---- start up ----

    def test_refuses_to_start_without_the_secret(self):
        config.JWT_SECRET_KEY = 'too-short'
        with self.assertRaises(RuntimeError):
            with TestClient(main.app):
                pass


if __name__ == '__main__':
    unittest.main()
