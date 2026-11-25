from decimal import Decimal

from services.orders.model import Order, OrderItem, OrderStatus
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from services.orders.schema import ApplyDiscountRequest
from services.orders.service import OrderService

def test_apply_discount_recalculates_order_total():
    db=MagicMock(spec=Session)
    discount=ApplyDiscountRequest(promo_code="SAVE10")
    order=Order(
        status=OrderStatus.OPEN,
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("5.00"),
        tax_gst=Decimal("5.00"),
        tax_qst=Decimal("9.98"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("114.98"),
    )
    order.items = [OrderItem(line_total=Decimal("100.00"))]

    applied = OrderService().apply_discount(db, order, discount)

    assert applied is True
    assert order.discount_amount == Decimal("10.00")
    assert order.total_amount == Decimal("104.98")
    db.commit.assert_called_once()