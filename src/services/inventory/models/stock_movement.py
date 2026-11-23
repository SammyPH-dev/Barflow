"""
Stock Movement Data Model Module

This module defines the StockMovement database model.
It is a log of every change made to the quantity of a lot.

The log is used to:
- give back an item removed from a client order (- on the POS) to the same lots it was taken from;
- keep a trace of losses and manual adjustments;
- stop the offline POS from deducting twice when it sends the same request again
  (one button press id per + or - press).

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func,
)

from .base import Base
from .enums import MovementType


class StockMovement(Base):
    __tablename__ = 'stock_movement'
    __table_args__ = (
        Index('ix_stock_movement_order', '_order_id'),
        # one press can touch many lots, so the button press id is unique per (press, lot)
        UniqueConstraint('_button_press_id', '_lot_stock_id', name='uq_movement_press_lot'),
    )

    _id = Column(Integer, primary_key=True, autoincrement=True)
    _lot_stock_id = Column(Integer, ForeignKey('lot_stock._id'), nullable=False)
    _type = Column(Enum(MovementType), nullable=False)
    # negative = the stock goes down, positive = the stock goes up
    _quantity_change = Column(Numeric(12, 3), nullable=False)
    # id of the client order in the order service (no foreign key, the table is in another service)
    _order_id = Column(Integer, nullable=True)
    _button_press_id = Column(String(64), nullable=True)
    _reason = Column(String(255), nullable=True)
    # id of the user (no foreign key, the users are not in this service). Only the id, no personal data (Loi 25)
    _user_id = Column(Integer, nullable=True)
    _created_at = Column(DateTime, nullable=False, server_default=func.now())
