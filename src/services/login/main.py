"""
bruno

Barflow Login Service entry point.

This module initializes and configures the FastAPI application responsible for
the Barflow login service. It creates the application instance, registers the
login router containing authentication routes, and starts the Uvicorn server
when the module is executed directly.

Attributes:
    app (FastAPI): The FastAPI application instance for the login service.
    router (APIRouter): The router containing the service's login endpoints.

Running:
    Execute this module directly to start the service locally:

        python -m src.services.login.main

Server configuration:
    Host: 127.0.0.1
    Port: 8001
"""

from fastapi import FastAPI
import uvicorn

from src.services.login.router import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Barflow Login Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
