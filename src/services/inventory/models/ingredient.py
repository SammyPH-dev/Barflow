"""
Ingredient Data Model Module

This module defines the Ingredient database model (spec: Ingredient: name, mesureUnit, shelfLife).
An ingredient owns many stock lots.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
License: Proprietary
"""

from decimal import Decimal

from sqlalchemy import Column, Enum, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base
from .enums import MesureUnit


class Ingredient(Base):
    __tablename__ = 'ingredient'
    _id = Column(Integer, primary_key=True, autoincrement=True)
    _name = Column(String(100), nullable=False, unique=True)
    _mesure_unit = Column(Enum(MesureUnit), nullable=False)
    # a reorder alert is sent when the usable stock drops below this value
    _reorder_threshold = Column(Numeric(12, 3), nullable=False, default=Decimal('0'))
    # number of days the ingredient lasts after it is ordered, used to calculate
    # the expiry date of its lot. None means it never expires (ex: a sealed bottle of alcohol)
    _shelf_life_days = Column(Integer, nullable=True)

    # list of the stock lots received for this ingredient
    # Similar to a join-table
    _lots = relationship(
        # reference to class LotStock(Base)
        'LotStock',
        backref='_ingredient',
        cascade='all, delete-orphan'
    )
