"""
Inventory Service Entry Point

This module creates the FastAPI application of the inventory service.
The API Gateway sends the inventory requests to this application.

Run it from the src folder:
    uvicorn services.inventory.main:app --port 8002

The DATABASE_URL environment variable must be set before the first request
(ex: mysql+pymysql://user:password@host/database).

Author: Zacchary Bedard-Chenier
Date: 22/11/2026
Version: 1.0
"""

from fastapi import FastAPI

from .routers import router

app = FastAPI(title='Barflow Inventory Service')

app.include_router(router)
