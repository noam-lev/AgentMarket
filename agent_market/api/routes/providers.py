from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from agent_market.schemas.provider import ProviderRegister, ProviderOut
from agent_market.services.provider_logic import (
    register_provider_db, authenticate_provider, create_access_token, get_provider_by_email_db
)
from agent_market.api.deps import get_database #, get_current_provider (to be implemented)
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=ProviderOut, status_code=status.HTTP_201_CREATED)
async def register_provider(
    provider_data: ProviderRegister,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    logger.info(f"Attempting to register new provider with email: {provider_data.email}")
    existing_provider = await get_provider_by_email_db(db, provider_data.email)
    if existing_provider:
        logger.warning(f"Registration failed: Email '{provider_data.email}' already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
    new_provider = await register_provider_db(db, provider_data)
    if not new_provider:
        logger.error(f"Failed to register provider '{provider_data.email}' due to internal error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register provider due to an internal error."
        )
    logger.info(f"Provider '{new_provider.email}' registered successfully with ID: {new_provider.id}")
    return new_provider

@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    logger.info(f"Attempting to log in provider with email: {form_data.username}")
    provider = await authenticate_provider(db, form_data.username, form_data.password)
    if not provider:
        logger.warning(f"Login failed: Incorrect credentials for email '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(provider.id)})
    logger.info(f"Provider '{form_data.username}' logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

# Placeholder for /me endpoint (requires get_current_provider dependency)
# @router.get("/me", response_model=ProviderOut)
# async def read_current_provider(
#     current_provider: Annotated[ProviderOut, Depends(get_current_provider)]
# ):
#     logger.info(f"Accessing /me endpoint for provider ID: {current_provider.id}")
#     return current_provider
