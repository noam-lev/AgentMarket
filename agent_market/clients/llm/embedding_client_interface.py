from abc import ABC, abstractmethod
from typing import List

class AbstractEmbeddingClient(ABC):
    """
    Abstract Base Class (Interface) for all LLM embedding clients.
    """
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a numerical embedding vector for the given text.
        Args:
            text: The input text string to embed.
        Returns:
            A list of floats representing the embedding vector.
        Raises:
            Exception: If embedding generation fails due to API errors, invalid input, etc.
        """
        pass 