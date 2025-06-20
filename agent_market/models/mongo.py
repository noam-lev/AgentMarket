from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from agent_market.core.config import settings
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDB:
    """
    Manages the asynchronous MongoDB client and database connection.
    Ensures a single client instance is used across the application.
    """
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """
        Establishes a connection to the MongoDB database.
        This method should be called during application startup.
        """
        if self.client is None:
            try:
                logger.info(f"Connecting to MongoDB with URI: '{settings.MONGO_URI}'")
                self.client = AsyncIOMotorClient(settings.MONGO_URI)
                self.database = self.client.get_default_database()
                await self.database.command("ping")
                logger.info(f"Successfully connected to MongoDB database: '{self.database.name}'")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise e

    async def close(self):
        """
        Closes the MongoDB client connection.
        This method should be called during application shutdown.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")
        else:
            logger.warning("Attempted to close MongoDB connection but client was not initialized.")

# Global instance
db = MongoDB()
