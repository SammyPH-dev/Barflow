from fastapi import FastAPI
from src.services.recommender.router import router as recommendations_router
app = FastAPI(title="Barflow recommendation API")

app.include_router(recommendations_router)