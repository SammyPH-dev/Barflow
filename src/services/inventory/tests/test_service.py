"""
Inventory Service Unit Tests Module

This module tests the business logic of the inventory service (stock levels, deductions,
returns, adjustments) with an in-memory SQLite database.

Run from the "src" folder:  python -m unittest discover -s services/inventory/tests -t .
Note: SQLite ignores the row locks (FOR UPDATE), the locks can only be tested on MariaDB.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

import unittest
import warnings
from datetime import date, timedelta
from decimal import Decimal as D

from sqlalchemy import create_engine
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session

from services.inventory.models import (
    Base, Ingredient, LotStock, MesureUnit, MovementType, StockMovement,
)
from services.inventory.schemas.stock_update import (
    AdjustmentDbSchema, DeductionDbSchema, DeductionItemDbSchema, ReturnDbSchema,
)
from services.inventory.services import (
    adjustment_service, client_order_service, movement_service, stock_service,
)
from services.inventory.services.errors import InvalidOperationError, NotFoundError

# SQLite stores decimals as floats and warns about it, the warning is not useful here
warnings.simplefilter('ignore', SAWarning)

TODAY = date(2026, 11, 17)


def deduction(order_id, button_press_id, quantities):
    """deduction(1, 'k', {1: 50}) -> deduction of 50 of the ingredient with id 1."""
    return DeductionDbSchema(
        order_id=order_id,
        button_press_id=button_press_id,
        items=[DeductionItemDbSchema(ingredient_id=i, quantity=q) for i, q in quantities.items()],
    )


def returning(order_id, button_press_id, quantities):
    """returning(1, 'k', {1: 50}) -> gives back 50 of the ingredient with id 1."""
    return ReturnDbSchema(
        order_id=order_id,
        button_press_id=button_press_id,
        items=[DeductionItemDbSchema(ingredient_id=i, quantity=q) for i, q in quantities.items()],
    )


class InventoryTestCase(unittest.TestCase):
    """Base class: every test gets an empty in-memory database with two ingredients."""

    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.s = Session(self.engine)

        # two ingredients used by most of the tests
        self.vodka = Ingredient(_name='Vodka', _mesure_unit=MesureUnit.ML,
                                _reorder_threshold=100)
        self.lime = Ingredient(_name='Lime', _mesure_unit=MesureUnit.UNIT,
                               _reorder_threshold=0)
        self.s.add_all([self.vodka, self.lime])
        self.s.flush()

    def tearDown(self):
        self.s.close()
        self.engine.dispose()

    def lot(self, ingredient, quantity, exp_in_days=None):
        lot = LotStock(
            _ingredient_id=ingredient._id, _quantity=D(quantity), _reception_date=TODAY,
            _exp_date=None if exp_in_days is None else TODAY + timedelta(days=exp_in_days),
        )
        self.s.add(lot)
        self.s.flush()
        return lot


class StockLevelTests(InventoryTestCase):
    def test_expired_and_empty_lots_are_not_usable(self):
        self.lot(self.vodka, 500, exp_in_days=10)
        self.lot(self.vodka, 300, exp_in_days=-1)   # expired
        self.lot(self.vodka, 0, exp_in_days=10)     # empty
        level = stock_service.get_stock_level(self.s, self.vodka._id, TODAY)
        self.assertEqual(level['usable_quantity'], D('500'))
        self.assertEqual(level['next_expiry'], TODAY + timedelta(days=10))

    def test_lot_expiring_today_is_usable(self):
        self.lot(self.vodka, 200, exp_in_days=0)
        level = stock_service.get_stock_level(self.s, self.vodka._id, TODAY)
        self.assertEqual(level['usable_quantity'], D('200'))

    def test_is_usable_matches_the_sql_filter(self):
        self.assertTrue(self.lot(self.vodka, 1, exp_in_days=0).is_usable(TODAY))
        self.assertFalse(self.lot(self.vodka, 1, exp_in_days=-1).is_usable(TODAY))
        self.assertFalse(self.lot(self.vodka, 0).is_usable(TODAY))

    def test_ingredient_without_lot_shows_zero(self):
        level = stock_service.get_stock_level(self.s, self.lime._id, TODAY)
        self.assertEqual(level['usable_quantity'], 0)
        self.assertIsNone(level['next_expiry'])

    def test_unknown_ingredient(self):
        with self.assertRaises(NotFoundError):
            stock_service.get_stock_level(self.s, 999, TODAY)

    def test_alerts_only_below_threshold(self):
        self.lot(self.vodka, 50)      # below 100
        self.lot(self.lime, 1)        # threshold 0 -> never alerts
        alerts = stock_service.get_all_alerts(self.s, TODAY)
        self.assertEqual([alert['name'] for alert in alerts], ['Vodka'])


class DeductionTests(InventoryTestCase):
    def test_deducts_earliest_expiry_first_across_lots(self):
        late = self.lot(self.vodka, 500, exp_in_days=30)
        soon = self.lot(self.vodka, 100, exp_in_days=3)
        never = self.lot(self.vodka, 500)  # no expiry date: used last
        result = client_order_service.deduct(self.s, deduction(1, 'k1', {self.vodka._id: D('250')}), today=TODAY)
        self.assertTrue(result['success'])
        self.assertEqual(soon._quantity, 0)
        self.assertEqual(late._quantity, D('350'))
        self.assertEqual(never._quantity, D('500'))

    def test_insufficient_stock_deducts_nothing(self):
        vodka_lot = self.lot(self.vodka, 100)
        lime_lot = self.lot(self.lime, 1)
        result = client_order_service.deduct(
            self.s, deduction(1, 'k1', {self.vodka._id: D('40'), self.lime._id: D('2')}), today=TODAY)
        self.assertFalse(result['success'])
        self.assertEqual([s['ingredient_id'] for s in result['shortages']], [self.lime._id])
        # all or nothing: the vodka was not deducted either
        self.assertEqual((vodka_lot._quantity, lime_lot._quantity), (D('100'), D('1')))
        self.assertEqual(self.s.query(StockMovement).count(), 0)

    def test_expired_stock_does_not_count(self):
        self.lot(self.vodka, 500, exp_in_days=-2)
        result = client_order_service.deduct(self.s, deduction(1, 'k1', {self.vodka._id: D('10')}), today=TODAY)
        self.assertFalse(result['success'])
        self.assertEqual(result['shortages'][0]['available'], 0)

    def test_replay_with_same_key_does_not_deduct_twice(self):
        lot = self.lot(self.vodka, 500)
        request = deduction(1, 'k1', {self.vodka._id: D('100')})
        client_order_service.deduct(self.s, request, today=TODAY)
        result = client_order_service.deduct(self.s, request, today=TODAY)
        self.assertTrue(result['success'])
        self.assertEqual(lot._quantity, D('400'))

    def test_same_order_can_add_several_items(self):
        # each + press has its own button press id, so the same order can deduct many times
        lot = self.lot(self.vodka, 500)
        client_order_service.deduct(self.s, deduction(1, 'k1', {self.vodka._id: D('100')}), today=TODAY)
        client_order_service.deduct(self.s, deduction(1, 'k2', {self.vodka._id: D('100')}), today=TODAY)
        self.assertEqual(lot._quantity, D('300'))

    def test_unknown_ingredient(self):
        with self.assertRaises(NotFoundError):
            client_order_service.deduct(self.s, deduction(1, 'k1', {999: D('1')}), today=TODAY)

    def test_alert_fires_only_when_threshold_is_crossed(self):
        self.lot(self.vodka, 150)  # threshold 100
        r1 = client_order_service.deduct(self.s, deduction(1, 'k1', {self.vodka._id: D('20')}), today=TODAY)
        self.assertEqual(r1['alerts'], [])        # 130, still fine
        r2 = client_order_service.deduct(self.s, deduction(2, 'k2', {self.vodka._id: D('40')}), today=TODAY)
        self.assertEqual(len(r2['alerts']), 1)    # 90, crossed
        r3 = client_order_service.deduct(self.s, deduction(3, 'k3', {self.vodka._id: D('10')}), today=TODAY)
        self.assertEqual(r3['alerts'], [])        # already below: not sent again

    def test_decimal_quantities_are_exact(self):
        lot = self.lot(self.vodka, '100.000')
        for i in range(3):
            client_order_service.deduct(self.s, deduction(i, f'k{i}', {self.vodka._id: D('0.100')}), today=TODAY)
        self.assertEqual(lot._quantity, D('99.700'))


class ReturnTests(InventoryTestCase):
    def test_return_goes_back_to_the_same_lots(self):
        soon = self.lot(self.vodka, 100, exp_in_days=3)
        late = self.lot(self.vodka, 500, exp_in_days=30)
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('250')}), today=TODAY)
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('250')}))
        self.assertEqual((soon._quantity, late._quantity), (D('100'), D('500')))

    def test_partial_return_starts_with_the_lot_used_last(self):
        soon = self.lot(self.vodka, 100, exp_in_days=3)
        late = self.lot(self.vodka, 500, exp_in_days=30)
        # 2 drinks of 75 ml: the first takes 75 from "soon",
        # the second takes the last 25 of "soon" and 50 from "late"
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('75')}), today=TODAY)
        client_order_service.deduct(self.s, deduction(1, 'd2', {self.vodka._id: D('75')}), today=TODAY)
        self.assertEqual((soon._quantity, late._quantity), (D('0'), D('450')))
        # one drink removed: the 50 go back to "late" first (the lot used last), then 25 to "soon"
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('75')}))
        self.assertEqual((soon._quantity, late._quantity), (D('25'), D('500')))
        # the second drink removed: everything is back where it was
        client_order_service.return_items(self.s, returning(1, 'r2', {self.vodka._id: D('75')}))
        self.assertEqual((soon._quantity, late._quantity), (D('100'), D('500')))

    def test_same_key_twice_returns_once(self):
        lot = self.lot(self.vodka, 500)
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('100')}), today=TODAY)
        client_order_service.deduct(self.s, deduction(1, 'd2', {self.vodka._id: D('100')}), today=TODAY)
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('100')}))
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('100')}))
        self.assertEqual(lot._quantity, D('400'))

    def test_cannot_return_more_than_the_order_took(self):
        lot = self.lot(self.vodka, 500)
        lime_lot = self.lot(self.lime, 10)
        client_order_service.deduct(
            self.s, deduction(1, 'd1', {self.vodka._id: D('100'), self.lime._id: D('1')}), today=TODAY)
        with self.assertRaises(InvalidOperationError):
            client_order_service.return_items(
                self.s, returning(1, 'r1', {self.vodka._id: D('50'), self.lime._id: D('2')}))
        # all or nothing: the vodka was not given back either
        self.assertEqual((lot._quantity, lime_lot._quantity), (D('400'), D('9')))

    def test_order_that_took_nothing_cannot_return(self):
        self.lot(self.vodka, 500)
        with self.assertRaises(InvalidOperationError):
            client_order_service.return_items(self.s, returning(42, 'r1', {self.vodka._id: D('1')}))
        self.assertEqual(self.s.query(StockMovement).count(), 0)

    def test_return_only_uses_the_lots_of_this_order(self):
        lot = self.lot(self.vodka, 500)
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('100')}), today=TODAY)
        # order 2 never took vodka, even if order 1 did
        with self.assertRaises(InvalidOperationError):
            client_order_service.return_items(self.s, returning(2, 'r1', {self.vodka._id: D('100')}))
        self.assertEqual(lot._quantity, D('400'))

    def test_unknown_ingredient(self):
        with self.assertRaises(NotFoundError):
            client_order_service.return_items(self.s, returning(1, 'r1', {999: D('1')}))

    def test_add_remove_add_again(self):
        lot = self.lot(self.vodka, 500)
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('100')}), today=TODAY)
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('100')}))
        client_order_service.deduct(self.s, deduction(1, 'd2', {self.vodka._id: D('100')}), today=TODAY)
        self.assertEqual(lot._quantity, D('400'))


class AdjustmentTests(InventoryTestCase):
    def adjust(self, lot_id, change, reason='count', **kwargs):
        data = AdjustmentDbSchema(lot_stock_id=lot_id, quantity_change=D(change), reason=reason)
        return adjustment_service.adjust_lot(self.s, data, today=TODAY, **kwargs)

    def test_negative_change_reduces_stock_and_is_logged(self):
        lot = self.lot(self.vodka, 500)
        movement, alert = self.adjust(lot._id, '-50', reason='spill', user_id=7)
        self.assertEqual(lot._quantity, D('450'))
        self.assertEqual((movement._type, movement._quantity_change, movement._user_id),
                         (MovementType.ADJUSTMENT, D('-50'), 7))

    def test_positive_change_adds_stock(self):
        lot = self.lot(self.vodka, 100)
        self.adjust(lot._id, '25')
        self.assertEqual(lot._quantity, D('125'))

    def test_change_cannot_make_stock_negative(self):
        lot = self.lot(self.vodka, 10)
        with self.assertRaises(InvalidOperationError):
            self.adjust(lot._id, '-11')
        self.assertEqual(lot._quantity, 10)

    def test_negative_change_can_trigger_alert(self):
        lot = self.lot(self.vodka, 150)
        movement, alert = self.adjust(lot._id, '-80', reason='broken')
        self.assertIsNotNone(alert)
        self.assertEqual(alert['usable_quantity'], D('70'))

    def test_unknown_lot(self):
        with self.assertRaises(NotFoundError):
            self.adjust(99, '-1')



class MovementTests(InventoryTestCase):
    def test_record_movement_changes_lot_and_logs_it(self):
        lot = self.lot(self.vodka, 100)
        movement = movement_service.record_movement(
            self.s, lot, D('-30'), MovementType.ADJUSTMENT, user_id=3, reason='spill')
        self.assertEqual(lot._quantity, D('70'))
        self.assertEqual((movement._lot_stock_id, movement._quantity_change, movement._reason),
                         (lot._id, D('-30'), 'spill'))

    def test_record_movement_refuses_negative_lot(self):
        lot = self.lot(self.vodka, 10)
        with self.assertRaises(InvalidOperationError):
            movement_service.record_movement(self.s, lot, D('-11'), MovementType.ADJUSTMENT)
        self.assertEqual(lot._quantity, D('10'))
        self.assertEqual(self.s.query(StockMovement).count(), 0)

    def test_every_change_type_is_listed_and_filtered(self):
        vodka_lot = self.lot(self.vodka, 500)
        lime_lot = self.lot(self.lime, 10)
        client_order_service.deduct(self.s, deduction(1, 'd1', {self.vodka._id: D('50')}), today=TODAY)
        client_order_service.return_items(self.s, returning(1, 'r1', {self.vodka._id: D('20')}))
        adjustment_service.adjust_lot(
            self.s, AdjustmentDbSchema(lot_stock_id=lime_lot._id, quantity_change=D('-2'),
                                       reason='spoiled'), today=TODAY)

        all_movements = movement_service.list_movements(self.s)
        # newest first
        self.assertEqual([m._type for m in all_movements],
                         [MovementType.ADJUSTMENT, MovementType.RETURN, MovementType.DEDUCTION])

        vodka_only = movement_service.list_movements(self.s, ingredient_id=self.vodka._id)
        self.assertEqual({m._lot_stock_id for m in vodka_only}, {vodka_lot._id})
        self.assertEqual(len(movement_service.list_movements(self.s, order_id=1)), 2)
        returns = movement_service.list_movements(self.s, movement_type=MovementType.RETURN)
        self.assertEqual([m._quantity_change for m in returns], [D('20')])
        self.assertEqual(len(movement_service.list_movements(self.s, limit=1)), 1)


if __name__ == '__main__':
    unittest.main()
