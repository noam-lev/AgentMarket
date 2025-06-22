from typing import List, Union, Type
from core.config import settings
import logging

from clients.llm.embedding_client_interface import AbstractEmbeddingClient
from clients.llm.openai_embedding_client import OpenAIEmbeddingClient
# from clients.llm.deepseek_embedding_client import DeepSeekEmbeddingClient

logger = logging.getLogger(__name__)

# Registry of embedding providers
EMBEDDING_CLIENTS: dict[str, Type[AbstractEmbeddingClient]] = {
    "openai": OpenAIEmbeddingClient,
    # "deepseek": DeepSeekEmbeddingClient,  # Uncomment when implemented
}

_embedding_client_instance: Union[AbstractEmbeddingClient, None] = None

async def initialize_embedding_client():
    global _embedding_client_instance
    provider = settings.EMBEDDING_PROVIDER.lower()
    client_cls = EMBEDDING_CLIENTS.get(provider)
    if client_cls is None:
        logger.error(f"Unsupported EMBEDDING_PROVIDER: '{provider}'. Please check settings.")
        raise ValueError(f"Unsupported embedding provider configured: {provider}")
    _embedding_client_instance = client_cls()
    logger.info(f"{provider.capitalize()} embedding client initialized and set as active.")

async def get_text_embedding(text: str) -> List[float]:
    global _embedding_client_instance
    if _embedding_client_instance is None:
        logger.error("Embedding client instance is not initialized. Call initialize_embedding_client() during app startup.")
        raise RuntimeError("Embedding client not initialized. Ensure `initialize_embedding_client()` is called in lifespan.")
    return await _embedding_client_instance.get_embedding(text)
