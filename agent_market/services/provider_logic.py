from motor.motor_asyncio import AsyncIOMotorDatabase
from agent_market.schemas.provider import ProviderRegister, ProviderLogin, ProviderOut, ProviderInDB
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from agent_market.core.config import settings
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Password hashing configuration using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password securely."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token for the provider."""
    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is not set in settings.")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_provider_by_email_db(db: AsyncIOMotorDatabase, email: str) -> Optional[ProviderInDB]:
    """Fetch a provider document by email."""
    provider_document = await db.providers.find_one({"email": email})
    if provider_document:
        provider_document["_id"] = str(provider_document["_id"])
        return ProviderInDB(**provider_document)
    return None

async def get_provider_by_id_db(db: AsyncIOMotorDatabase, provider_id: str) -> Optional[ProviderInDB]:
    """Fetch a provider document by ObjectId."""
    if not ObjectId.is_valid(provider_id):
        logger.warning(f"Attempted to retrieve provider with invalid ObjectId format: {provider_id}")
        return None
    provider_document = await db.providers.find_one({"_id": ObjectId(provider_id)})
    if provider_document:
        provider_document["_id"] = str(provider_document["_id"])
        return ProviderInDB(**provider_document)
    return None

async def register_provider_db(db: AsyncIOMotorDatabase, provider_data: ProviderRegister) -> Optional[ProviderOut]:
    """Register a new provider, hash password, store in DB, return ProviderOut."""
    hashed_password = get_password_hash(provider_data.password)
    provider_dict = provider_data.model_dump()
    provider_dict["password_hash"] = hashed_password
    del provider_dict["password"]
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    result = await db.providers.insert_one(provider_dict)
    created_provider_document = await db.providers.find_one({"_id": result.inserted_id})
    if created_provider_document:
        created_provider_document["id"] = str(created_provider_document["_id"])
        return ProviderOut(**created_provider_document)
    logger.error("Failed to retrieve newly registered provider document.")
    return None

async def authenticate_provider(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[ProviderInDB]:
    """Authenticate a provider by email and password."""
    provider = await get_provider_by_email_db(db, email)
    if not provider:
        logger.info(f"Authentication failed: Provider with email '{email}' not found.")
        return None
    if not verify_password(password, provider.password_hash):
        logger.info(f"Authentication failed: Incorrect password for provider '{email}'.")
        return None
    logger.info(f"Provider '{email}' authenticated successfully.")
    return provider
