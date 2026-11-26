"""
Stock Update Schema Module

This module defines the Pydantic schemas used to validate every request that changes the stock:
deductions and returns (sent by the order service when + or - is pressed on a client order on the POS),
manual adjustments (Manager only).

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from ..services import inventory_rules


# one ingredient of a client order item and the quantity the recipe needs
class DeductionItemDbSchema(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(gt=0, decimal_places=3)


# + pressed on the POS: all or nothing deduction of the ingredients of one item (recipe)
# button_press_id is unique for each press, also works with the offline POS
# send the same request again without deducting twice:
# If the POS goes offline after sending a deduction task to the server, it might not receive an answer back.
# So, it would be able to send the same + press more than once (same id)
# Each press gets one unique id but a retry reuses that same id.
# When the server sees an id it has already processed (press_already_processed() in client_order_service.py),
# it answers "OK" without deducting a second time.
class DeductionDbSchema(BaseModel):
    order_id: int
    button_press_id: str = Field(min_length=1, max_length=64)
    items: list[DeductionItemDbSchema] = Field(min_length=1)

    @field_validator('items')
    @classmethod
    def unique_ingredients(cls, value):
        return inventory_rules.validate_unique_ingredients(value)


# - pressed on the POS: gives back the ingredients of the item removed from the client order
# it inherits all fields from DeductionDbSchema
class ReturnDbSchema(DeductionDbSchema):
    pass


# manual correction of one lot (ex: after a physical count), manager only
class AdjustmentDbSchema(BaseModel):
    lot_stock_id: int
    quantity_change: Decimal = Field(decimal_places=3) # can be + or -
    reason: str = Field(min_length=1, max_length=255)

    @field_validator('quantity_change')
    @classmethod
    def change_not_zero(cls, value):
        return inventory_rules.validate_not_zero(value)

    @field_validator('reason')
    @classmethod
    def reason_not_blank(cls, value):
        return inventory_rules.validate_not_blank(value)
