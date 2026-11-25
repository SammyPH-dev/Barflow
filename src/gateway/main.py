from fastapi import FastAPI
from src.services.recommender.router import router as recommendations_router
app = FastAPI(title="Barflow API")

app.include_router(recommendations_router)

@app.get("/")
async def root():
    return {"message": "API is online"}