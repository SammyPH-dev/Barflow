"""
Stock Lot Data Model Module

This module defines the LotStock database model (spec: LotStock: quantity, receptionDate, expDate).
A lot is one received batch of one ingredient.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
License: Proprietary
"""

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, Integer, Numeric

from .base import Base


class LotStock(Base):
    __tablename__ = 'lot_stock'
    __table_args__ = (
        # the database itself refuses a negative quantity
        CheckConstraint('_quantity >= 0', name='ck_lot_stock_quantity_notneg'),
        # the deduction looks for the lots of an ingredient, the ones that expire first are deducted first
        Index('ix_lot_stock_ingredient_exp', '_ingredient_id', '_exp_date'),
    )

    _id = Column(Integer, primary_key=True, autoincrement=True)
    _ingredient_id = Column(Integer, ForeignKey('ingredient._id'), nullable=False)
    _quantity = Column(Numeric(12, 3), nullable=False) # ml / g / units
    _reception_date = Column(Date, nullable=False)
    # calculated from the shelf life of the ingredient, None means the lot never expires
    _exp_date = Column(Date, nullable=True)

    def is_usable(self, today):
        # a lot is usable only if quantity > 0 and it is not expired.
        return self._quantity > 0 and (self._exp_date is None or self._exp_date >= today)
