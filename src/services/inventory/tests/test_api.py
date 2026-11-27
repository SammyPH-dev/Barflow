"""
Inventory API Tests Module

This module tests the HTTP routes of the inventory service: roles, status codes,
JSON responses and commit / rollback of the changes.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

import unittest
import warnings
from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.inventory.database_connection import get_session
from services.inventory.models import Base
from services.inventory.routers import router

warnings.simplefilter('ignore', SAWarning)

URL = '/api/v1/inventory'
MANAGER = {'X-User-Id': '1', 'X-User-Role': 'manager'}
EMPLOYEE = {'X-User-Id': '2', 'X-User-Role': 'employee'}


class ApiTests(unittest.TestCase):
    def setUp(self):
        # StaticPool: every request uses the same in-memory database
        self.engine = create_engine(
            'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        factory = sessionmaker(self.engine, expire_on_commit=False)

        def test_session():
            with factory() as session:
                yield session

        app = FastAPI()
        app.include_router(router)
        # the routes use the test database instead of MariaDB
        app.dependency_overrides[get_session] = test_session
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def seed_vodka(self, quantity='500'):
        ingredient = self.client.post(f'{URL}/ingredients', headers=MANAGER, json={
            'name': 'Vodka', 'mesure_unit': 'ml', 'reorder_threshold': 100}).json()
        # every restock is a supplier order (one lot per line)
        self.client.post(f'{URL}/supplier-orders', headers=MANAGER, json={
            'lines': [{'ingredient_id': ingredient['id'], 'quantity': quantity, 'unit_price': '0.05'}]})
        return ingredient['id']

    def usable(self, ingredient_id):
        return self.client.get(f'{URL}/stock/{ingredient_id}', headers=EMPLOYEE).json()['usable_quantity']

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(f'{URL}/stock').status_code, 401)
        bad_role = {'X-User-Id': '1', 'X-User-Role': 'X'}
        self.assertEqual(self.client.get(f'{URL}/stock', headers=bad_role).status_code, 401)
        # the API Gateway always sends the role in lowercase
        uppercase = {'X-User-Id': '1', 'X-User-Role': 'MANAGER'}
        self.assertEqual(self.client.get(f'{URL}/stock', headers=uppercase).status_code, 401)

    def test_employee_cannot_use_manager_endpoints(self):
        for method, url, body in [
            ('post', '/ingredients', {'name': 'A', 'mesure_unit': 'ml'}),
            ('patch', '/ingredients/1', {'name': 'B'}),
            ('post', '/adjustments', {'lot_stock_id': 1, 'quantity_change': '1', 'reason': 'x'}),
            ('post', '/supplier-orders', {'lines': []}),
            ('get', '/alerts', None),
            ('get', '/movements', None),
            ('get', '/supplier-orders', None),
        ]:
            response = getattr(self.client, method)(
                URL + url, headers=EMPLOYEE, **({'json': body} if body else {}))
            self.assertEqual(response.status_code, 403, url)

    def test_employee_can_read_stock_and_ingredients(self):
        ingredient_id = self.seed_vodka()
        response = self.client.get(f'{URL}/stock/{ingredient_id}', headers=EMPLOYEE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['usable_quantity'], '500.000')  # text, never a float
        ingredients = self.client.get(f'{URL}/ingredients', headers=EMPLOYEE).json()['ingredients']
        self.assertEqual([i['name'] for i in ingredients], ['Vodka'])

    def test_add_then_remove_item_over_http(self):
        ingredient_id = self.seed_vodka()
        body = {'order_id': 1, 'button_press_id': 'd1',
                'items': [{'ingredient_id': ingredient_id, 'quantity': '450'}]}
        response = self.client.post(f'{URL}/deductions', headers=EMPLOYEE, json=body)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(response.json()['alerts']), 1)  # 50 < threshold 100
        self.assertEqual(self.usable(ingredient_id), '50.000')

        response = self.client.post(f'{URL}/returns', headers=EMPLOYEE, json={
            'order_id': 1, 'button_press_id': 'r1',
            'items': [{'ingredient_id': ingredient_id, 'quantity': '450'}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.usable(ingredient_id), '500.000')

        # removing it a second time: the order no longer holds that vodka
        again = self.client.post(f'{URL}/returns', headers=EMPLOYEE, json={
            'order_id': 1, 'button_press_id': 'r2',
            'items': [{'ingredient_id': ingredient_id, 'quantity': '450'}]})
        self.assertEqual(again.status_code, 409)

    def test_shortage_returns_200_success_false_and_changes_nothing(self):
        ingredient_id = self.seed_vodka('100')
        response = self.client.post(f'{URL}/deductions', headers=EMPLOYEE, json={
            'order_id': 1, 'button_press_id': 'd1',
            'items': [{'ingredient_id': ingredient_id, 'quantity': '101'}]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['shortages'][0]['available'], '100.000')
        self.assertEqual(self.usable(ingredient_id), '100.000')

    def test_error_codes(self):
        self.assertEqual(self.client.get(f'{URL}/stock/999', headers=MANAGER).status_code, 404)
        ingredient_id = self.seed_vodka('10')
        loss = self.client.post(f'{URL}/adjustments', headers=MANAGER,
                                json={'lot_stock_id': 1, 'quantity_change': '-11', 'reason': 'x'})
        self.assertEqual(loss.status_code, 409)  # more than the lot holds
        self.assertEqual(list(loss.json()), ['detail'])  # {"detail": "message"} only
        duplicate = self.client.post(f'{URL}/ingredients', headers=MANAGER,
                                     json={'name': 'Vodka', 'mesure_unit': 'ml'})
        self.assertEqual(duplicate.status_code, 409)
        negative = self.client.post(f'{URL}/deductions', headers=EMPLOYEE, json={
            'order_id': 1, 'button_press_id': 'k',
            'items': [{'ingredient_id': ingredient_id, 'quantity': '-1'}]})
        self.assertEqual(negative.status_code, 422)
        blank = self.client.post(f'{URL}/ingredients', headers=MANAGER,
                                 json={'name': '   ', 'mesure_unit': 'ml'})
        self.assertEqual(blank.status_code, 422)

    def test_failed_request_changes_nothing(self):
        ingredient_id = self.seed_vodka('10')
        # adjustment refused: the stock must be the same as before
        self.client.post(f'{URL}/adjustments', headers=MANAGER,
                         json={'lot_stock_id': 1, 'quantity_change': '-11', 'reason': 'x'})
        self.assertEqual(self.usable(ingredient_id), '10.000')

    def test_update_ingredient(self):
        ingredient_id = self.seed_vodka()
        response = self.client.patch(f'{URL}/ingredients/{ingredient_id}', headers=MANAGER,
                                     json={'reorder_threshold': 250})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reorder_threshold'], 250)
        self.assertEqual(response.json()['name'], 'Vodka')  # not sent, not changed
        empty = self.client.patch(f'{URL}/ingredients/{ingredient_id}', headers=MANAGER, json={})
        self.assertEqual(empty.status_code, 400)
        null_name = self.client.patch(f'{URL}/ingredients/{ingredient_id}', headers=MANAGER,
                                      json={'name': None})
        self.assertEqual(null_name.status_code, 409)
        unknown = self.client.patch(f'{URL}/ingredients/999', headers=MANAGER, json={'name': 'Gin'})
        self.assertEqual(unknown.status_code, 404)

    def test_adjustment_response(self):
        self.seed_vodka('150')
        response = self.client.post(f'{URL}/adjustments', headers=MANAGER, json={
            'lot_stock_id': 1, 'quantity_change': '-80', 'reason': 'count'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['movement']['quantity_change'], '-80.000')
        self.assertEqual(response.json()['movement']['type'], 'ADJUSTMENT')
        self.assertEqual(response.json()['alert']['usable_quantity'], '70.000')

    def test_movement_history(self):
        ingredient_id = self.seed_vodka('150')  # RESTOCK
        self.client.post(f'{URL}/adjustments', headers=MANAGER, json={
            'lot_stock_id': 1, 'quantity_change': '-10', 'reason': 'spill'})
        self.client.post(f'{URL}/deductions', headers=EMPLOYEE, json={
            'order_id': 4, 'button_press_id': 'd1',
            'items': [{'ingredient_id': ingredient_id, 'quantity': '40'}]})

        response = self.client.get(f'{URL}/movements', headers=MANAGER)
        self.assertEqual(response.status_code, 200)
        movements = response.json()['movements']
        self.assertEqual([m['type'] for m in movements], ['DEDUCTION', 'ADJUSTMENT', 'RESTOCK'])
        self.assertEqual(movements[0]['quantity_change'], '-40.000')
        self.assertEqual(movements[0]['order_id'], 4)

        filtered = self.client.get(f'{URL}/movements?type=ADJUSTMENT', headers=MANAGER).json()
        self.assertEqual([m['reason'] for m in filtered['movements']], ['spill'])
        today = date.today().isoformat()
        by_day = self.client.get(f'{URL}/movements?date_from={today}&date_to={today}', headers=MANAGER)
        self.assertEqual(len(by_day.json()['movements']), 3)
        self.assertEqual(self.client.get(f'{URL}/movements?type=X', headers=MANAGER).status_code, 422)

    def test_supplier_order_is_received_immediately(self):
        vodka_id = self.seed_vodka('10')
        lime_id = self.client.post(f'{URL}/ingredients', headers=MANAGER, json={
            'name': 'Lime', 'mesure_unit': 'unit', 'shelf_life_days': 10}).json()['id']

        response = self.client.post(f'{URL}/supplier-orders', headers=MANAGER, json={
            'lines': [
                {'ingredient_id': vodka_id, 'quantity': '700', 'unit_price': '0.05'},
                {'ingredient_id': lime_id, 'quantity': '24', 'unit_price': '0.35'},
            ]})
        self.assertEqual(response.status_code, 201)
        order = response.json()
        self.assertEqual(order['total'], '43.40')  # 35.00 + 8.40
        self.assertEqual(order['placed_by'], 1)
        self.assertEqual(order['status'], 'RECEIVED')
        self.assertNotIn('supplier_id', order)
        # one lot for each line
        lot_ids = [line['lot_stock_id'] for line in order['lines']]
        self.assertEqual(len(set(lot_ids)), 2)
        self.assertNotIn(None, lot_ids)
        # the stock went up right away
        self.assertEqual(self.usable(vodka_id), '710.000')
        self.assertEqual(self.usable(lime_id), '24.000')
        # the expiry date of the lime is the order day + its shelf life
        stock = self.client.get(f'{URL}/stock/{lime_id}', headers=EMPLOYEE).json()
        self.assertEqual(stock['next_expiry'], (date.today() + timedelta(days=10)).isoformat())

        orders = self.client.get(f'{URL}/supplier-orders', headers=MANAGER).json()['supplier_orders']
        # newest first: this order, then the one seed_vodka() placed
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]['id'], order['id'])
        one = self.client.get(f'{URL}/supplier-orders/{order["id"]}', headers=MANAGER)
        self.assertEqual(one.json()['status'], 'RECEIVED')

    def test_failed_supplier_order_changes_nothing(self):
        vodka_id = self.seed_vodka('10')
        # second line is refused (unknown ingredient): the first line must not be added either
        response = self.client.post(f'{URL}/supplier-orders', headers=MANAGER, json={
            'lines': [
                {'ingredient_id': vodka_id, 'quantity': '700', 'unit_price': '0.05'},
                {'ingredient_id': 999, 'quantity': '5', 'unit_price': '0.05'},
            ]})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.usable(vodka_id), '10.000')
        # only the order placed by seed_vodka() exists
        orders = self.client.get(f'{URL}/supplier-orders', headers=MANAGER).json()['supplier_orders']
        self.assertEqual(len(orders), 1)

    def test_supplier_order_needs_at_least_one_line(self):
        response = self.client.post(f'{URL}/supplier-orders', headers=MANAGER, json={'lines': []})
        self.assertEqual(response.status_code, 422)

    def test_shelf_life_is_stored_on_the_ingredient(self):
        created = self.client.post(f'{URL}/ingredients', headers=MANAGER, json={
            'name': 'Milk', 'mesure_unit': 'ml', 'shelf_life_days': 7})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()['shelf_life_days'], 7)
        updated = self.client.patch(f'{URL}/ingredients/{created.json()["id"]}', headers=MANAGER,
                                    json={'shelf_life_days': 5})
        self.assertEqual(updated.json()['shelf_life_days'], 5)
        invalid = self.client.post(f'{URL}/ingredients', headers=MANAGER, json={
            'name': 'Cream', 'mesure_unit': 'ml', 'shelf_life_days': 0})
        self.assertEqual(invalid.status_code, 422)


if __name__ == '__main__':
    unittest.main()
