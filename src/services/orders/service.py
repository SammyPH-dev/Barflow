from typing import Optional

from sqlalchemy import delete, select

from services.orders.model import Order, OrderStatus
from services.orders.models import OrderItem
from services.orders.schema import OrderCreate, OrderItemCreate, OrderStatusUpdate, OrderitemUpdate
from sqlalchemy.orm import Session
from decimal import Decimal


class OrderService():
    def __init__(self) -> None:
        pass

    # crud operations
    def create_order(self, db: Session, data: OrderCreate) -> Order:
        if data is None:
            return
        
        order = Order(
            table_number=data.table_number,
            status=OrderStatus.OPEN,
            subtotal=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_gst=Decimal("0.00"),
            tax_qst=Decimal("0.00"),
            tip_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            notes=data.notes,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order

    def fetch_order(self, db: Session, id:int) -> Optional[Order]:
        return db.get(Order, id)
        

    def fetch_all_orders(self, db: Session) -> list[Order]:
        stmt = select(Order).order_by(Order.id)
        return list(db.scalars(stmt).all())

    def update_order_status(
            self, db:Session, \
            order_id:int,
            data:OrderStatusUpdate, ) -> Optional[Order]:
                order = db.get(Order, order_id)

                if order is None:
                    return

                order.status=data.status

                if data.tip_amount is not None:
                    order.tip_amount = data.tip_amount
                    order.total_amount = (
                        order.subtotal
                        - order.discount_amount
                        + order.tax_gst
                        + order.tax_qst
                        + data.tip_amount
                    )

                db.add(order)
                db.commit()
                db.refresh(order)

                return order

    def delete_order(self, db:Session, id:int) -> bool:
        order=db.get(Order, id)

        if order is None:
            return False

        db.delete(order)
        db.commit
        return True

    def add_order_item(
        self,
        db:Session,
        order_id:int,
        items: list[OrderItemCreate],
    ) -> Optional[list[OrderItem]]:
        
        order=db.get(Order, order_id)
        if order is None:
            return None

        created_items=[]

        for item_data in items:
            unit_price=Lookup_recipe_price(item_data.recipes_id)

            if unit_price is None:
                return None

            item = OrderItem(
                order_id=order_id,
                recipes_id=item_data.recipes_id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                line_total=unit_price*item_data.quantity,
                special_instructions=item_data.special_instructions
            )

            db.add(item)
            created_items.append(item)

        db.flush()
        self.recalculate_totals(db, order)
        db.commit()

        for item in created_items:
            db.refresh(item)

        return created_items

    def update_order_item(
            self,
            db:Session,
            order_item_id:int,
            data: OrderitemUpdate,
    ) -> Optional[OrderItem]:
        item=db.get(OrderItem, order_item_id)
        if item is None:
            return None

        if data.quantity is not None:
            item.quanity = data.quantity
            item.line_total = item.unti_price * data.quantity

        if data.special_instructions is not None:
            item.special_instructions = data.special_instructions

        db.flush()
        self.recalculate_totals(db, item.order)
        db.commit()
        db.refresh(item)
        return item

    def delete_order_item(self):
        pass


    # item operations
    def apply_discount(self):
        pass

    def update_tip(self):
        pass

    def recalculate_totals(self):
        order.subtotal = sum(
            item.line_total for item in order.items
        )

        order.total_amount=(
            order.subtotal
            - order.discount_amount
            + order.tax_gst
            + order.tax_qst
            + order.tip_amount
        )





    

    