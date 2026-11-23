"""
Supplier Order Data Model Module

This module defines the SupplierOrder database model
and its lines, LigneSupplierOrder (quantity, unitPrice).
Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from .base import Base
from .enums import SupplierOrderStatus


# restocking order to refill the inventory, placed by a Manager
# for now, it is received immediately. Pressing "Order" on the POS adds all its lots to the inventory
class SupplierOrder(Base):
    __tablename__ = 'supplier_order'
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # id of the Manager. The user table is in another service, so no foreign key? (note to self: check with teammates)
    _placed_by = Column(Integer, nullable=False)
    _order_date = Column(DateTime, nullable=False, server_default=func.now())
    _status = Column(Enum(SupplierOrderStatus), nullable=False, default=SupplierOrderStatus.RECEIVED)
    _total = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))

    _lines = relationship(
        # reference to class LigneSupplierOrder(Base)
        # like a join-table
        'LigneSupplierOrder',
        backref='_order',
        cascade='all, delete-orphan',
        order_by='LigneSupplierOrder._id'
    )


# class for the individual lines that will be contained in _lines
class LigneSupplierOrder(Base):
    __tablename__ = 'ligne_supplier_order'
    _id = Column(Integer, primary_key=True, autoincrement=True)
    _supplier_order_id = Column(Integer, ForeignKey('supplier_order._id'), nullable=False)
    _ingredient_id = Column(Integer, ForeignKey('ingredient._id'), nullable=False)
    # the lot created from this line (one lot per line), filled when the order is placed
    _lot_stock_id = Column(Integer, ForeignKey('lot_stock._id'), nullable=True)
    _quantity = Column(Numeric(12, 3), nullable=False)
    _unit_price = Column(Numeric(10, 2), nullable=False)
