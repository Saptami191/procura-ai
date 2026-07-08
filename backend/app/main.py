from fastapi import FastAPI
from loguru import logger

app = FastAPI(
    title="Procura AI",
    description="Enterprise AI Workforce Platform - API",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Procura AI - Enterprise AI Workforce Platform"}


@app.get("/health")
async def health() -> dict[str, str]:
    logger.debug("Health check called")
    return {"status": "healthy"}
