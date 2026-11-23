"""
Ingredient Schema Module

This module defines the Pydantic schemas used to validate the ingredient data
sent to the inventory service (creation and partial update).

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""


from pydantic import BaseModel, Field, field_validator

from ..models.enums import MesureUnit
from ..services import inventory_rules


class IngredientDbSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    mesure_unit: MesureUnit
    reorder_threshold: int = Field(default=0, ge=0)
    # days the ingredient lasts after it is ordered, absent = never expires
    shelf_life_days: int | None = Field(default=None, ge=1)

    @field_validator('name')
    @classmethod
    def name_not_blank(cls, value):
        return inventory_rules.validate_not_blank(value)


# for updating an ingredient
# every field can be absent, only the fields that are sent will be changed
class IngredientUpdateDbSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    mesure_unit: MesureUnit | None = None
    reorder_threshold: int | None = Field(default=None, ge=0)
    shelf_life_days: int | None = Field(default=None, ge=1)  # null = never expires

    @field_validator('name')
    @classmethod
    def name_not_blank(cls, value):
        return inventory_rules.validate_not_blank(value)
