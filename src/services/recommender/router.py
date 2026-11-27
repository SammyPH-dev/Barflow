from fastapi import APIRouter
from .service import get_recommendations, get_expiring_stocks, get_recipes_containing, get_expiring_recipe_recommendations
from .schemas import StatusResponse, Recommendations, Stock, Recipe, ExpiringDrink


router = APIRouter(
    prefix="/api/v1/recommendations",
)

@router.get("/", response_model=StatusResponse)
async def root() -> StatusResponse:
    return StatusResponse(message="API is online")

@router.get("/drinks", response_model=Recommendations)
async def recommendations() -> Recommendations:
    return await get_recommendations()


@router.get("/expiring_stocks", response_model=list[Stock])
async def expiring_stocks() -> list[Stock]:
    return await get_expiring_stocks()

@router.get("/expiring_recipes", response_model=list[ExpiringDrink])
async def expiring_recipes() -> list[ExpiringDrink]:
    return await get_expiring_recipe_recommendations()