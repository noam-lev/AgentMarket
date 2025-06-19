from motor.motor_asyncio import AsyncIOMotorDatabase
from agent_market.models.mongo import db
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from agent_market.core.config import settings
from agent_market.services.provider_logic import get_provider_by_id_db
from agent_market.schemas.provider import ProviderInDB, ProviderOut
from typing import Annotated
import logging

async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides the MongoDB database instance.
    Raises HTTP 500 if the database is not initialized (e.g., startup failed).
    """
    if db.database is None:
        raise HTTPException(status_code=500, detail="Database not initialized. Application may not have started correctly.")
    return db.database

# JWT auth dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/providers/token")
logger = logging.getLogger(__name__)

async def get_current_provider(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ProviderInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not settings.JWT_SECRET_KEY:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        provider_id = payload.get("sub")
        if not isinstance(provider_id, str) or not provider_id:
            logger.warning("JWT payload missing or invalid 'sub' (provider ID) claim.")
            raise credentials_exception
    except (JWTError, ValidationError) as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception
    provider = await get_provider_by_id_db(db, provider_id)
    if provider is None:
        logger.warning(f"Authenticated provider ID '{provider_id}' not found in database.")
        raise credentials_exception
    logger.info(f"Successfully authenticated provider: {provider.email} (ID: {provider.id})")
    return provider
