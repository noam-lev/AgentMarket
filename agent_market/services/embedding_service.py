"""
Embedding and Semantic Search Logic for AgentMarket

This module provides functions to generate embeddings for service descriptions, compute vector similarity, and perform semantic search over all services in the database.

Functions:
    - generate_service_embedding: Generate an embedding for a service description.
    - cosine_similarity: Compute cosine similarity between two vectors.
    - semantic_search_services: Given a query, return services ranked by semantic similarity.

For MVP, all vector search is done in-memory. For production, use a vector DB or MongoDB Atlas Vector Search.
"""

from typing import List, Tuple
from core.embeddings import get_text_embedding
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.service import ServiceOut, ServiceInDB
import numpy as np
import logging

logger = logging.getLogger(__name__)

async def generate_service_embedding(description: str) -> List[float]:
    """
    Orchestrates the generation of an embedding for a service description.
    Returns a list of floats representing the embedding.
    """
    if not description:
        logger.warning("Attempted to generate embedding for empty description.")
        return []
    try:
        embedding = await get_text_embedding(description)
        return embedding
    except Exception as e:
        logger.error(f"Error in generate_service_embedding for description: '{description[:50]}...': {e}")
        raise

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculates the cosine similarity between two vectors.
    Returns a float between -1 and 1, where 1 is perfect similarity.
    """
    if not vec1 or not vec2:
        return 0.0
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    dot_product = np.dot(vec1_np, vec2_np)
    magnitude_vec1 = np.linalg.norm(vec1_np)
    magnitude_vec2 = np.linalg.norm(vec2_np)
    if magnitude_vec1 == 0 or magnitude_vec2 == 0:
        return 0.0
    return dot_product / (magnitude_vec1 * magnitude_vec2)

async def semantic_search_services(db: AsyncIOMotorDatabase, query_text: str) -> List[Tuple[ServiceOut, float]]:
    """
    Performs a semantic search for services based on a natural language query.
    Returns a list of (ServiceOut, similarity_score) tuples, sorted by similarity descending.
    """
    if not query_text:
        logger.warning("Semantic search query text is empty.")
        return []
    logger.info(f"Generating embedding for search query: '{query_text[:50]}...'")
    try:
        query_embedding = await get_text_embedding(query_text)
    except Exception as e:
        logger.error(f"Failed to generate embedding for search query: {e}")
        return []
    all_services_in_db: List[ServiceInDB] = []
    cursor = db.services.find({})
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        if "embedding" in doc and isinstance(doc["embedding"], list) and all(isinstance(x, float) for x in doc["embedding"]):
            all_services_in_db.append(ServiceInDB(**doc))
        else:
            logger.warning(f"Service ID {doc['id']} has invalid or missing embedding and will be skipped from search results.")
    ranked_services: List[Tuple[ServiceOut, float]] = []
    for service_in_db in all_services_in_db:
        if service_in_db.embedding and len(service_in_db.embedding) > 0:
            similarity = cosine_similarity(query_embedding, service_in_db.embedding)
            service_out = ServiceOut(**service_in_db.model_dump())
            ranked_services.append((service_out, similarity))
    ranked_services.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Semantic search returned {len(ranked_services)} results for query: '{query_text}'")
    return ranked_services
