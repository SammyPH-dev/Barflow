from common.base import Base

import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

#test
#defines how data is stored in your MariaDB database (SQLAlchemy ORM tables)

class OrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    table_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True
    )
    

    #Foreign keys linking to sibling domain tables
    bartender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    discount_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("discounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.OPEN,
        nullable=False,
        index=True
    )

    #monetary field stored with exact decimal precision for Mariadb
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    tax_gst: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        default=Decimal("0.00"),
        nullable=False
    )

    tax_qst: Mapped[Decimal] = mapped_column(
        Numeric(10,2), 
        default=Decimal("0.00"), 
        nullable=False
    )

    tip_amount: Mapped[Decimal] = mapped_column(
        Numeric(10,2), 
        default=Decimal("0.00"), 
        nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10,2), 
        default=Decimal("0.00"), 
        nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False,
    )

    #Relationships
    items: Mapped[List[OrderItem]] = relationship(
        "OrderItem",
        back_populates = "order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    recipes_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id",
        ondelete="RESTRICT"),
        nullable=False, index=True
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    special_instructions: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=False
    )



    #Relationship
    order: Mapped[Order] = relationship(
        "Order", back_populates="items"
    )




