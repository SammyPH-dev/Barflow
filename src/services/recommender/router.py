from fastapi import APIRouter
from .service import get_recommendations


router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

@router.get("/drinks")
async def recommendations():
    return get_recommendations()