"""
Inventory Routes Package

This package groups the routes of the inventory service under /api/v1/inventory,
so the application only has to include one router: app.include_router(router)

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import APIRouter

from .. import config
from . import adjustment_router, ingredient_router, movement_router, restock_router, stock_router

router = APIRouter(prefix=config.API_PREFIX)

router.include_router(stock_router.router)
router.include_router(adjustment_router.router)
router.include_router(ingredient_router.router)
router.include_router(restock_router.router)
router.include_router(movement_router.router)
