"""
Service Business Logic for AgentMarket

This module provides all core CRUD (Create, Read, Update, Delete) operations for API service listings in the AgentMarket platform.
It integrates embedding generation for semantic search, usage tracking, and robust error handling/logging.

Functions:
    - create_service_db: Create a new service listing, generate and store its embedding.
    - get_service_by_id_db: Retrieve a service by its unique ID.
    - get_all_services_db: Retrieve all service listings.
    - update_service_db: Update an existing service, regenerate embedding if description changes.
    - delete_service_db: Delete a service by its ID.
    - increment_service_usage_db: Increment the usage count for a service.

All functions expect an AsyncIOMotorDatabase instance and use Pydantic schemas for input/output.
Embeddings are generated via the embedding_service module.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from agent_market.schemas.service import ServiceCreate, ServiceOut, ServiceInDB
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

from agent_market.services.embedding_service import generate_service_embedding

async def create_service_db(db: AsyncIOMotorDatabase, service_data: ServiceCreate) -> Optional[ServiceOut]:
    """
    Creates a new service listing in the database.
    Generates an embedding for the service description before saving.
    Returns the created ServiceOut object, or None if creation fails.
    """
    logger.info(f"Attempting to create service: {service_data.name} for provider: {service_data.provider_id}")
    service_dict = service_data.model_dump(by_alias=False)
    try:
        service_dict["embedding"] = await generate_service_embedding(service_data.description)
        logger.info(f"Embedding generated for service: {service_data.name}")
    except Exception as e:
        logger.error(f"Failed to generate embedding for service '{service_data.name}': {e}")
        service_dict["embedding"] = []
    service_dict['api']['endpoint'] = str(service_dict['api']['endpoint'])
    service_dict["usage_count"] = 0
    service_dict["created_at"] = datetime.now(timezone.utc)
    service_dict["updated_at"] = datetime.now(timezone.utc)
    result = await db.services.insert_one(service_dict)
    created_document = await db.services.find_one({"_id": result.inserted_id})
    if created_document:
        created_document["id"] = str(created_document["_id"])
        logger.info(f"Service '{service_data.name}' created successfully with ID: {created_document['id']}")
        return ServiceOut(**created_document)
    logger.error(f"Failed to retrieve newly created service document for '{service_data.name}'.")
    return None

async def get_service_by_id_db(db: AsyncIOMotorDatabase, service_id: str) -> Optional[ServiceOut]:
    """
    Retrieves a single service document by its unique ID.
    Returns ServiceOut object if found, otherwise None.
    """
    if not ObjectId.is_valid(service_id):
        logger.warning(f"Attempted to get service with invalid ID format: {service_id}")
        return None
    service_document = await db.services.find_one({"_id": ObjectId(service_id)})
    if service_document:
        service_document["id"] = str(service_document["_id"])
        return ServiceOut(**service_document)
    return None

async def get_all_services_db(db: AsyncIOMotorDatabase) -> List[ServiceOut]:
    """
    Retrieves all service documents from the database.
    Returns a list of ServiceOut objects.
    """
    services: List[ServiceOut] = []
    cursor = db.services.find({})
    async for document in cursor:
        document["id"] = str(document["_id"])
        services.append(ServiceOut(**document))
    logger.info(f"Retrieved {len(services)} services from the database.")
    return services

async def update_service_db(db: AsyncIOMotorDatabase, service_id: str, update_data: dict) -> Optional[ServiceOut]:
    """
    Updates an existing service document in the database.
    If description is updated, a new embedding will be generated.
    Returns the updated ServiceOut object, or None if update fails.
    """
    if not ObjectId.is_valid(service_id):
        logger.warning(f"Attempted to update service with invalid ID format: {service_id}")
        return None
    if 'api' in update_data and 'endpoint' in update_data['api']:
        update_data['api']['endpoint'] = str(update_data['api']['endpoint'])
    update_fields = {k: v for k, v in update_data.items() if v is not None}
    update_fields["updated_at"] = datetime.now(timezone.utc)
    if "description" in update_fields:
        try:
            update_fields["embedding"] = await generate_service_embedding(update_fields["description"])
            logger.info(f"Embedding regenerated for service ID: {service_id}")
        except Exception as e:
            logger.error(f"Failed to regenerate embedding for service ID '{service_id}': {e}")
            pass
    result = await db.services.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": update_fields}
    )
    if result.modified_count == 1:
        logger.info(f"Service ID {service_id} updated successfully.")
        return await get_service_by_id_db(db, service_id)
    logger.warning(f"Service ID {service_id} not found or no changes applied during update.")
    return None

async def delete_service_db(db: AsyncIOMotorDatabase, service_id: str) -> bool:
    """
    Deletes a service document from the database by its ID.
    Returns True if deleted, False otherwise.
    """
    if not ObjectId.is_valid(service_id):
        logger.warning(f"Attempted to delete service with invalid ID format: {service_id}")
        return False
    result = await db.services.delete_one({"_id": ObjectId(service_id)})
    if result.deleted_count == 1:
        logger.info(f"Service ID {service_id} deleted successfully.")
        return True
    logger.warning(f"Service ID {service_id} not found for deletion.")
    return False

async def increment_service_usage_db(db: AsyncIOMotorDatabase, service_id: str) -> bool:
    """
    Increments the usage_count for a given service.
    Returns True if incremented, False otherwise.
    """
    if not ObjectId.is_valid(service_id):
        logger.warning(f"Attempted to increment usage for service with invalid ID format: {service_id}")
        return False
    result = await db.services.update_one(
        {"_id": ObjectId(service_id)},
        {"$inc": {"usage_count": 1}}
    )
    if result.modified_count == 1:
        logger.info(f"Service ID {service_id} usage count incremented.")
        return True
    logger.warning(f"Service ID {service_id} not found for usage increment.")
    return False
