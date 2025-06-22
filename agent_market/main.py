from contextlib import asynccontextmanager
from fastapi import FastAPI
from agent_market.core.config import settings
from agent_market.models.mongo import db
from agent_market.core.embeddings import initialize_embedding_client
from agent_market.api.routes import providers  # services router import commented out
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated.")
    await db.connect()
    logger.info("Database connection established for AgentMarket MVP.")
    try:
        await initialize_embedding_client()
        logger.info(f"Embedding client initialized using provider: {settings.EMBEDDING_PROVIDER}")
    except Exception as e:
        logger.error(f"Failed to initialize embedding client: {e}. Application cannot start without embedding capability.", exc_info=True)
        raise
    yield
    logger.info("Application shutdown initiated.")
    await db.close()
    logger.info("Database connection closed for AgentMarket MVP.")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# app.include_router(services.router, prefix="/api/services", tags=["Services"])  # Commented out, not implemented yet
app.include_router(providers.router, prefix="/api/providers", tags=["Providers"])

@app.get("/")
async def read_root():
    """Returns a welcome message from the AgentMarket MVP."""
    return {"message": "Welcome to AgentMarket MVP! The AI-Native API Marketplace."}
