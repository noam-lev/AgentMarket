import openai
from typing import List
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from agent_market.core.config import settings
from agent_market.clients.llm.embedding_client_interface import AbstractEmbeddingClient

logger = logging.getLogger(__name__)

async def before_sleep_log(retry_state):
    logger.warning(
        f"Retrying OpenAI embedding due to: {retry_state.outcome.exception()} (attempt {retry_state.attempt_number})"
    )

class OpenAIEmbeddingClient(AbstractEmbeddingClient):
    """
    Concrete implementation of AbstractEmbeddingClient for OpenAI's embedding models.
    """
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set. Cannot initialize OpenAIEmbeddingClient.")
            raise ValueError("OPENAI_API_KEY is not configured for OpenAI embedding provider.")
        self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAIEmbeddingClient initialized successfully.")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError)),
        before_sleep=before_sleep_log
    )
    async def _get_embedding_with_retry(self, text: str) -> List[float]:
        response = await self._client.embeddings.create(
            input=[text],
            model="text-embedding-ada-002"
        )
        if not response.data or not isinstance(response.data, list) or len(response.data) == 0:
            logger.error(f"OpenAI API returned empty or invalid data structure. Response: {response}")
            raise ValueError("OpenAI API returned unexpected response format for embedding.")
        embedding = response.data[0].embedding
        if not isinstance(embedding, list) or not all(isinstance(x, float) or isinstance(x, int) for x in embedding):
            logger.error(f"OpenAI embedding is not a list of floats/integers. Embedding: {embedding}")
            raise ValueError("OpenAI embedding response format is invalid: not a list of numbers.")
        return embedding

    async def get_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            logger.warning("Attempted to generate embedding for empty or whitespace-only text using OpenAI. Returning empty list.")
            return []
        try:
            return await self._get_embedding_with_retry(text)
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API error during embedding generation: {e.status_code} - {e.response}")
            raise Exception(f"Failed to generate embedding with OpenAI: {e}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error during embedding generation: {e}")
            raise Exception(f"Failed to generate embedding with OpenAI: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred with OpenAI embedding client: {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred during embedding generation with OpenAI: {e}") 