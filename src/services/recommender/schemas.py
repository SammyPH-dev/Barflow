from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Response from the service's root endpoint."""

    message: str


class Stock(BaseModel):
    """Usable inventory information for one ingredient."""

    ingredient_id: int
    name: str
    mesure_unit: str  # Keep the spelling used by the inventory API.
    usable_quantity: Decimal = Field(ge=0)
    reorder_threshold: Decimal = Field(ge=0)
    below_threshold: bool
    next_expiry: date | None


class RecipeIngredient(BaseModel):
    """One ingredient and the amount required for one serving."""

    ingredient_id: int
    quantity: Decimal = Field(gt=0)
    unit: str


class Recipe(BaseModel):
    """A recipe returned by the temporary recipe lookup."""

    recipe_id: int
    name: str
    ingredient_ids: list[RecipeIngredient]


class PopularDrink(BaseModel):
    """A drink recommended because of its sales."""

    recipe_id: int
    name: str
    quantity_ordered: int | None = Field(default=None, ge=0)


class ExpiringDrink(BaseModel):
    """A drink recommended because an ingredient approaches expiry."""

    recipe_id: int
    name: str
    reason: str


class Recommendations(BaseModel):
    """The two recommendation lists returned together."""

    expiring_drinks: list[ExpiringDrink]
    popular_drinks: list[PopularDrink]

class RecipeSalesCount(BaseModel):
    """Number of servings sold for one recipe"""

    recipe_id: int
    quantity_ordered: int = Field(ge=0)