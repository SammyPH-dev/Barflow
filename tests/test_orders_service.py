from decimal import Decimal

from services.orders.model import Order, OrderItem, OrderStatus
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from services.orders.schema import ApplyDiscountRequest, OrderCreate, OrderItemCreate, OrderStatusUpdate, OrderitemUpdate
from services.orders.service import OrderService, lookup_recipe_price

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

def test_apply_discount_rejects_unknown_code():
    db=MagicMock(spec=Session)
    order = Order(
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("5.00"),
        tax_gst=Decimal("5.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
    )

    applied=OrderService().apply_discount(
        db, order, ApplyDiscountRequest(promo_code="UNKNOWN")
    )

    assert applied is False
    assert order.discount_amount == Decimal("5.00")
    assert order.total_amount == Decimal("100.00")
    db.commit.assert_not_called()

def test_add_order_item_on_valid_recipe():
    db=MagicMock(spec=Session)
    order = Order(
        status=OrderStatus.OPEN,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )
    order.items=[]
    db.get.return_value = order

    result = OrderService().add_order_item(
        db,
        order_id=1,
        items=[OrderItemCreate(recipes_id=1, quantity=2)],
    )

    assert result is not None
    assert len(result) == 1
    assert result[0].unit_price==Decimal("10.00")
    assert result[0].line_total==Decimal("20.00")
    assert order.subtotal == Decimal("20.00")
    assert order.total_amount == Decimal("20.00")
    db.commit.assert_called_once()

def test_add_order_rejects_unknown_recipe():
    db=MagicMock(spec=Session)
    order = Order(
        status=OrderStatus.OPEN,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )
    order.items=[]
    db.get.return_value = order

    result = OrderService().add_order_item(
        db,
        order_id=1,
        items=[OrderItemCreate(recipes_id=3, quantity=2)],
    )

    assert result is None
    assert order.subtotal == Decimal("0.00")
    assert order.total_amount == Decimal("0.00")
    db.commit.assert_not_called()

def test_add_order_items_missing_order():
    db=MagicMock(spec=Session)
    db.get.return_value = None
    result = OrderService().add_order_item(
        db,
        order_id=1,
        items=[],
    )

    assert result is None
    db.commit.assert_not_called()

def test_update_order_item_on_valid_item():
    db=MagicMock(spec=Session)
    order = Order(
        status=OrderStatus.OPEN,
        subtotal=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
    )
    item = OrderItem(
        order_id=1,
        recipes_id=1,
        quantity=1,
        unit_price=Decimal("10.00"),
        line_total=Decimal("10.00"),
        special_instructions=None,
        order=order,
    )
    db.get.return_value = item

    result = OrderService().update_order_item(
        db,
        order_item_id=1,
        data=OrderitemUpdate(quantity=3),
    )
    assert result is item
    assert item.line_total == Decimal("30.00")
    assert order.subtotal == Decimal("30.00")
    assert order.total_amount == Decimal("30.00")
    db.commit.assert_called_once()

def test_update_order_item_on_missing_item():
    db=MagicMock(spec=Session)
    db.get.return_value = None

    result = OrderService().update_order_item(
        db,
        order_item_id=1,
        data=OrderitemUpdate(quantity=3),
    )
    assert result is None
    db.flush.assert_not_called()
    db.commit.assert_not_called()

def test_update_order_item_special_instructions_only():
    db=MagicMock(spec=Session)
    order = Order(
        status=OrderStatus.OPEN,
        subtotal=Decimal("20.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("20.00"),
    )
    item = OrderItem(
        order_id=1,
        recipes_id=1,
        quantity=2,
        unit_price=Decimal("10.00"),
        line_total=Decimal("20.00"),
        special_instructions=None,
        order=order,
    )
    db.get.return_value = item

    result = OrderService().update_order_item(
        db,
        order_item_id=1,
        data=OrderitemUpdate(special_instructions="On the rocks"),
    )

    assert result is item
    assert item.special_instructions == "On the rocks"
    assert item.quantity == 2
    assert item.unit_price == Decimal("10.00")
    assert item.line_total == Decimal("20.00")
    assert order.subtotal == Decimal("20.00")
    assert order.total_amount == Decimal("20.00")
    db.commit.assert_called_once()

def test_delete_order_item():
    db=MagicMock(spec=Session)
    order = Order(
        id=1,
        status=OrderStatus.OPEN,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )

    item = OrderItem(
        order_id=1,
        recipes_id=1,
        quantity=2,
        unit_price=Decimal("10.00"),
        line_total=Decimal("20.00"),
        special_instructions=None,
        order=order,
    )

    result = OrderService().delete_order_item(db, item)

    assert result is True
    assert item not in order.items
    assert order.subtotal == Decimal("0.00")
    assert order.total_amount == Decimal("0.00")
    db.commit.assert_called_once()

def test_delete_order_without_items():
    db=MagicMock(spec=Session)
    order = Order(
        id=1,
        status=OrderStatus.OPEN,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )
    db.get.return_value = order
    result = OrderService().delete_order(db, 1)

    assert result is True
    db.get.assert_called_once_with(Order, 1)
    db.delete.assert_called_once_with(order)
    db.commit.assert_called_once()

def test_delete_order_missing_order():
    db=MagicMock(spec=Session)
    db.get.return_value = None

    result = OrderService().delete_order(db, id=1)

    assert result is False
    db.get.assert_called_once_with(Order, 1)
    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_update_order_status():
    db=MagicMock(spec=Session)
    order = Order(
        id=1,
        status=OrderStatus.OPEN,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_gst=Decimal("0.00"),
        tax_qst=Decimal("0.00"),
        tip_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )

    db.get.return_value=order
    result = OrderService().update_order_status(
        db,
        order_id=1,
        data=OrderStatusUpdate(status=OrderStatus.IN_PROGRESS, tip_amount=Decimal("5.00")),
    )
    assert result is not None
    assert result.status == OrderStatus.IN_PROGRESS
    assert result.tip_amount == Decimal("5.00")
    db.get.assert_called_once_with(Order, 1)
    db.add.assert_called_once_with(order)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(order)

def test_create_order_with_missing_data_returns_none():
    db = MagicMock(spec=Session)

    result = OrderService().create_order(db, data=None) # pyright: ignore[reportArgumentType]

    assert result is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

def test_create_order():
    db=MagicMock(spec=Session)

    result = OrderService().create_order(
        db,
        data=OrderCreate(table_number="1", notes="Test order"),
    )

    assert result is not None
    db.add.assert_called_once()
    created_order=db.add.call_args.args[0]

    assert isinstance(created_order, Order)
    assert result is created_order
    assert result.table_number == "1"
    assert result.status == OrderStatus.OPEN
    assert result.subtotal == Decimal("0.00")
    assert result.notes == "Test order"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(created_order)

def test_create_order_with_invalid_data():
    db=MagicMock(spec=Session)
    result = OrderService().create_order(
        db,
        data=None,  # pyright: ignore[reportArgumentType]
    )

    assert result is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

def test_update_order_status_missing_order_returns_none():
    db = MagicMock(spec=Session)
    db.get.return_value = None

    result = OrderService().update_order_status(
        db,
        order_id=1,
        data=OrderStatusUpdate(status=OrderStatus.IN_PROGRESS),
    )

    assert result is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

def test_fetch_all_order():
    db=MagicMock(spec=Session)
    db.get_return_value=


