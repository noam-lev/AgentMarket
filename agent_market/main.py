from contextlib import asynccontextmanager
from fastapi import FastAPI
from agent_market.core.config import settings
from agent_market.models.mongo import db
from agent_market.api.routes import providers  # Add services when implemented
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated.")
    await db.connect()
    logger.info("Database connection established for AgentMarket MVP.")
    yield
    logger.info("Application shutdown initiated.")
    await db.close()
    logger.info("Database connection closed for AgentMarket MVP.")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Include routers
app.include_router(providers.router, prefix="/api/providers", tags=["Providers"])
# app.include_router(services.router, prefix="/api/services", tags=["Services"])  # Uncomment when services implemented

@app.get("/")
async def read_root():
    """Returns a welcome message from the AgentMarket MVP."""
    return {"message": "Welcome to AgentMarket MVP! The AI-Native API Marketplace."}

