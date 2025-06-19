from motor.motor_asyncio import AsyncIOMotorDatabase
from agent_market.models.mongo import db
from fastapi import HTTPException, status

async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides the MongoDB database instance.
    Raises HTTP 500 if the database is not initialized (e.g., startup failed).
    """
    if db.database is None:
        raise HTTPException(status_code=500, detail="Database not initialized. Application may not have started correctly.")
    return db.database
