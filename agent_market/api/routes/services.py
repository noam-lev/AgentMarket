"""
Service API Endpoints for AgentMarket

This module exposes HTTP endpoints for service management and semantic search.
All endpoints use Pydantic schemas for input/output and enforce authentication/ownership where needed.

Endpoints:
    - POST   /api/services/                 (Create service, returns ServiceOut)
    - GET    /api/services/{service_id}     (Get service by ID, returns ServiceOut)
    - PUT    /api/services/{service_id}     (Update service, returns ServiceOut)
    - DELETE /api/services/{service_id}     (Delete service, returns message dict)
    - GET    /api/services/search           (Semantic search, returns List[ServiceOut])
    - POST   /api/services/{service_id}/usage (Report usage, returns message dict)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List
from bson import ObjectId

from agent_market.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from agent_market.api.deps import get_database, get_current_provider
from agent_market.services.service_logic import (
    create_service_db, 
    get_service_by_id_db, 
    get_all_services_db, 
    update_service_db, 
    delete_service_db,
    increment_service_usage_db
)
from agent_market.services.embedding_service import semantic_search_services
from agent_market.schemas.provider import ProviderOut

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service_listing(
    service_data: ServiceCreate,
    current_provider: Annotated[ProviderOut, Depends(get_current_provider)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ServiceOut:
    """
    Create a new API service listing. Returns the created ServiceOut.
    """
    logger.info(f"Provider {current_provider.id} attempting to create service: {service_data.name}")
    if service_data.provider_id != current_provider.id:
        logger.warning(f"Auth mismatch: Provider {current_provider.id} tried to create service for {service_data.provider_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create services for your own provider ID."
        )
    if service_data.openapi_spec:
        try:
            import json
            json.loads(service_data.openapi_spec)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid OpenAPI Spec JSON format.")
    created_service = await create_service_db(db, service_data)
    if not created_service:
        logger.error(f"Failed to create service '{service_data.name}' for provider {current_provider.id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service listing."
        )
    return created_service

@router.get("/search", response_model=List[ServiceOut])
async def search_services_for_agents(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    query: str = Query(..., min_length=3, description="Natural language query for AI agent semantic search.")
) -> List[ServiceOut]:
    """
    Semantic search for API services. Returns a ranked list of ServiceOut.
    """
    logger.info(f"AI Agent search query received: '{query}'")
    ranked_results = await semantic_search_services(db, query)
    services_only = [service_out for service_out, _ in ranked_results[:10]]
    logger.info(f"Returned {len(services_only)} semantic search results for query: '{query}'")
    return services_only

@router.get("/{service_id}", response_model=ServiceOut)
async def get_service_details(
    service_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ServiceOut:
    """
    Get service details by ID. Returns ServiceOut.
    """
    logger.info(f"Retrieving details for service ID: {service_id}")
    service = await get_service_by_id_db(db, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
    return service

@router.put("/{service_id}", response_model=ServiceOut)
async def update_service_listing(
    service_id: str,
    update_data: ServiceUpdate,
    current_provider: Annotated[ProviderOut, Depends(get_current_provider)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> ServiceOut:
    """
    Update an existing service listing. Returns the updated ServiceOut.
    """
    logger.info(f"Provider {current_provider.id} attempting to update service: {service_id}")
    existing_service = await get_service_by_id_db(db, service_id)
    if not existing_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
    if existing_service.provider_id != current_provider.id:
        logger.warning(f"Auth mismatch: Provider {current_provider.id} tried to update service {service_id} owned by {existing_service.provider_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own services."
        )
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"provider_id"})
    updated_service = await update_service_db(db, service_id, update_dict)
    if not updated_service:
        logger.error(f"Failed to update service '{service_id}' for provider {current_provider.id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update service listing."
        )
    return updated_service

@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service_listing(
    service_id: str,
    current_provider: Annotated[ProviderOut, Depends(get_current_provider)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> dict:
    """
    Delete a service listing. Returns a confirmation message dict.
    """
    logger.info(f"Provider {current_provider.id} attempting to delete service: {service_id}")
    existing_service = await get_service_by_id_db(db, service_id)
    if not existing_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
    if existing_service.provider_id != current_provider.id:
        logger.warning(f"Auth mismatch: Provider {current_provider.id} tried to delete service {service_id} owned by {existing_service.provider_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own services."
        )
    if not await delete_service_db(db, service_id):
        logger.error(f"Failed to delete service '{service_id}' for provider {current_provider.id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete service."
        )
    return {"message": "Service deleted successfully."}

@router.post("/{service_id}/usage", status_code=status.HTTP_200_OK)
async def report_service_usage(
    service_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> dict:
    """
    Report usage of a service. Returns a confirmation message dict.
    """
    logger.info(f"Usage reported for service ID: {service_id}")
    if not ObjectId.is_valid(service_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid service ID format.")
    if not await increment_service_usage_db(db, service_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found to increment usage.")
    return {"message": "Usage reported successfully."}
