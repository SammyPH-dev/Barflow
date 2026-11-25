from pydantic import BaseModel

class PopularDrink(BaseModel):
    recipe_id: int
    name: str
    quantity_ordered: int | None = None

class ExpiringDrink(BaseModel):
    recipe_id: int
    name: str
    reason: str

class Recommendations(BaseModel):
    expiring_drinks: list[ExpiringDrink]
    popular_drinks: list[PopularDrink]