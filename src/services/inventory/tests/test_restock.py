"""
Restock Unit Tests Module

This module tests the supplier orders (orders to refill the inventory, not client orders)
and the reception of stock, with an in-memory SQLite database.

For now, a supplier order is received immediately when it is placed.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

import unittest
from datetime import timedelta
from decimal import Decimal as D

from sqlalchemy import select

from services.inventory.default_ingredients import default_ingredients_if_db_empty
from services.inventory.models import (
    Ingredient, LotStock, MesureUnit, MovementType, StockMovement, SupplierOrder,
    SupplierOrderStatus,
)
from services.inventory.schemas.supplier_order import SupplierOrderDbSchema, SupplierOrderLineDbSchema
from services.inventory.services import stock_service, supplier_order_service
from services.inventory.services.errors import NotFoundError

from .test_service import TODAY, InventoryTestCase


class RestockTests(InventoryTestCase):
    def setUp(self):
        super().setUp()
        # vodka never expires (no shelf life), lime lasts 14 days
        self.lime._shelf_life_days = 14
        self.s.flush()

    def order(self, *lines):
        """order((ingredient_id, quantity, unit_price), ...) -> placed order."""
        data = SupplierOrderDbSchema(
            lines=[SupplierOrderLineDbSchema(
                       ingredient_id=line[0], quantity=line[1], unit_price=line[2])
                   for line in lines],
        )
        return supplier_order_service.create_order(self.s, data, manager_id=1, today=TODAY)

    def usable(self, ingredient):
        return stock_service.get_stock_level(self.s, ingredient._id, TODAY)['usable_quantity']

    def test_total_is_exact_decimal(self):
        order = self.order((self.vodka._id, D('0.333'), D('10.00')),   # 3.33
                           (self.lime._id, D('12'), D('0.35')))        # 4.20
        self.assertEqual(order._total, D('7.53'))

    def test_order_is_received_immediately(self):
        order = self.order((self.vodka._id, D('700'), D('0.05')))
        self.assertEqual(order._status, SupplierOrderStatus.RECEIVED)
        self.assertEqual(order._placed_by, 1)
        line = order._lines[0]
        self.assertIsNotNone(line._lot_stock_id)
        self.assertEqual(self.usable(self.vodka), D('700'))

        lot = self.s.get(LotStock, line._lot_stock_id)
        self.assertEqual((lot._ingredient_id, lot._reception_date, lot._exp_date),
                         (self.vodka._id, TODAY, None))
        movement = self.s.query(StockMovement).one()
        self.assertEqual((movement._type, movement._quantity_change, movement._user_id),
                         (MovementType.RESTOCK, D('700'), 1))

    def test_each_line_becomes_its_own_lot(self):
        order = self.order((self.vodka._id, D('700'), D('0.05')),
                           (self.lime._id, D('24'), D('0.35')))
        lot_ids = [line._lot_stock_id for line in order._lines]
        self.assertEqual(len(set(lot_ids)), 2)
        self.assertEqual(self.s.query(LotStock).count(), 2)
        self.assertEqual(self.usable(self.vodka), D('700'))
        self.assertEqual(self.usable(self.lime), D('24'))

    def test_three_item_types_make_three_lots(self):
        # 3 rum, 3 maple syrup, 15 limes: one lot for each item type
        rum = Ingredient(_name='Rum', _mesure_unit=MesureUnit.UNIT)
        syrup = Ingredient(_name='Maple syrup', _mesure_unit=MesureUnit.UNIT)
        self.s.add_all([rum, syrup])
        self.s.flush()
        order = self.order((rum._id, D('3'), D('14.00')),
                           (syrup._id, D('3'), D('9.00')),
                           (self.lime._id, D('15'), D('1.00')))
        lots = [self.s.get(LotStock, line._lot_stock_id) for line in order._lines]
        # the lines are sorted by ingredient name: Lime, Maple syrup, Rum
        self.assertEqual([(lot._ingredient_id, lot._quantity) for lot in lots],
                         [(self.lime._id, D('15')), (syrup._id, D('3')), (rum._id, D('3'))])
        self.assertEqual(self.s.query(LotStock).count(), 3)

    def test_order_can_have_many_lines(self):
        ingredients = [Ingredient(_name=f'Ingredient {i}', _mesure_unit=MesureUnit.ML) for i in range(25)]
        self.s.add_all(ingredients)
        self.s.flush()
        order = self.order(*[(ingredient._id, D('10'), D('1.00')) for ingredient in ingredients])
        self.assertEqual(len(order._lines), 25)
        self.assertEqual(self.s.query(LotStock).count(), 25)
        self.assertEqual(order._total, D('250.00'))

    def test_second_order_adds_a_new_lot(self):
        self.order((self.vodka._id, D('100'), D('1')))
        self.order((self.vodka._id, D('50'), D('1')))
        self.assertEqual(self.s.query(LotStock).count(), 2)
        self.assertEqual(self.usable(self.vodka), D('150'))

    def test_unknown_ingredient(self):
        with self.assertRaises(NotFoundError):
            self.order((999, D('1'), D('1')))
        self.assertEqual(self.s.query(SupplierOrder).count(), 0)

    def test_exp_date_is_order_day_plus_shelf_life(self):
        milk = Ingredient(_name='Milk', _mesure_unit=MesureUnit.ML, _shelf_life_days=7)
        self.s.add(milk)
        self.s.flush()
        order = self.order((milk._id, D('2000'), D('0.01')),
                           (self.lime._id, D('10'), D('0.35')),
                           (self.vodka._id, D('750'), D('0.05')))
        lots = [self.s.get(LotStock, line._lot_stock_id) for line in order._lines]
        # the lines are sorted by ingredient name: Lime, Milk, Vodka
        self.assertEqual([lot._exp_date for lot in lots],
                         [TODAY + timedelta(days=14), TODAY + timedelta(days=7), None])

    def test_lines_are_sorted_by_ingredient_name(self):
        apple = Ingredient(_name='apple juice', _mesure_unit=MesureUnit.ML)
        self.s.add(apple)
        self.s.flush()
        order = self.order((self.vodka._id, D('750'), D('0.05')),
                           (self.lime._id, D('10'), D('0.35')),
                           (apple._id, D('1000'), D('0.01')))
        # the lowercase name is still sorted first
        self.assertEqual([line._ingredient_id for line in order._lines],
                         [apple._id, self.lime._id, self.vodka._id])

        # the order read back from the database keeps the same order
        self.s.expire_all()
        reloaded = supplier_order_service.get_order(self.s, order._id)
        self.assertEqual([line._ingredient_id for line in reloaded._lines],
                         [apple._id, self.lime._id, self.vodka._id])

    def test_lot_is_expired_once_its_shelf_life_is_over(self):
        self.order((self.lime._id, D('10'), D('0.35')))
        last_day = TODAY + timedelta(days=14)
        self.assertEqual(stock_service.get_stock_level(self.s, self.lime._id, last_day)['usable_quantity'], D('10'))
        after = last_day + timedelta(days=1)
        self.assertEqual(stock_service.get_stock_level(self.s, self.lime._id, after)['usable_quantity'], 0)

    def test_get_order_and_list_newest_first(self):
        first = self.order((self.vodka._id, D('10'), D('1')))
        second = self.order((self.lime._id, D('5'), D('1')))
        self.assertEqual(supplier_order_service.get_order(self.s, first._id)._id, first._id)
        self.assertEqual([o._id for o in supplier_order_service.get_all_orders(self.s)],
                         [second._id, first._id])
        with self.assertRaises(NotFoundError):
            supplier_order_service.get_order(self.s, 999)


class DefaultIngredientsTests(InventoryTestCase):
    def test_default_ingredients_are_added_only_to_an_empty_table(self):
        # the base class already added 2 ingredients, so nothing is added
        default_ingredients_if_db_empty(self.s)
        self.assertEqual(self.s.query(Ingredient).count(), 2)

        self.s.query(Ingredient).delete()
        default_ingredients_if_db_empty(self.s)
        count = self.s.query(Ingredient).count()
        self.assertGreater(count, 0)
        default_ingredients_if_db_empty(self.s)  # a second call changes nothing
        self.assertEqual(self.s.query(Ingredient).count(), count)

    def test_default_ingredients_have_a_shelf_life_where_it_makes_sense(self):
        self.s.query(Ingredient).delete()
        default_ingredients_if_db_empty(self.s)
        milk = self.s.scalars(select(Ingredient).where(Ingredient._name == 'Lait')).one()
        self.assertEqual(milk._shelf_life_days, 7)
        rum = self.s.scalars(select(Ingredient).where(Ingredient._name == 'Rhum')).one()
        self.assertIsNone(rum._shelf_life_days)


if __name__ == '__main__':
    unittest.main()
