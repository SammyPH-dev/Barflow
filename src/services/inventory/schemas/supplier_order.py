"""
Supplier Order Schema Module

This module defines the Pydantic schemas used to validate the supplier orders

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from decimal import Decimal

from pydantic import BaseModel, Field


# one line of a supplier order = one ingredient, which becomes one lot in the inventory
# the expiry date of the lot is not sent, it is calculated from the shelf life of the ingredient
class SupplierOrderLineDbSchema(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_price: Decimal = Field(ge=0, decimal_places=2)


# an order can have as many lines (ingredients) as needed, but at least one
class SupplierOrderDbSchema(BaseModel):
    lines: list[SupplierOrderLineDbSchema] = Field(min_length=1)
