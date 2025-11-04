"""
MongoDB Configuration for Building Machinery AI Chatbot
Handles connection pooling, read/write concerns, and connection settings
"""

from typing import Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, WriteConcern, ReadConcern, ReadPreference
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)


class MongoDBConfig:
    """MongoDB connection configuration and management"""

    # Connection Pool Settings (DB-011)
    MIN_POOL_SIZE = 5
    MAX_POOL_SIZE = 50  # Supports 40-50 concurrent users
    MAX_IDLE_TIME_MS = 30000  # 30 seconds
    WAIT_QUEUE_TIMEOUT_MS = 5000  # 5 seconds

    # Timeout Settings
    CONNECTION_TIMEOUT_MS = 10000  # 10 seconds
    SERVER_SELECTION_TIMEOUT_MS = 5000  # 5 seconds

    # Database Name
    DATABASE_NAME = "chatbot"

    # Collection Names
    USERS_COLLECTION = "users"
    CONVERSATIONS_COLLECTION = "conversations"
    AUDIT_LOGS_COLLECTION = "audit_logs"
    DOCUMENT_METADATA_COLLECTION = "document_metadata"

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize MongoDB configuration

        Args:
            connection_string: MongoDB Atlas connection string (mongodb+srv://...)
                             If None, reads from MONGODB_URI environment variable
        """
        self.connection_string = connection_string or os.getenv("MONGODB_URI")
        if not self.connection_string:
            raise ValueError("MongoDB connection string not provided")

        self.client: Optional[AsyncIOMotorClient] = None
        self.sync_client: Optional[MongoClient] = None

    def get_connection_options(self) -> dict:
        """
        Get MongoDB connection options with pooling and concerns

        Returns:
            Dictionary of connection options
        """
        return {
            # Connection Pool Configuration
            "minPoolSize": self.MIN_POOL_SIZE,
            "maxPoolSize": self.MAX_POOL_SIZE,
            "maxIdleTimeMS": self.MAX_IDLE_TIME_MS,
            "waitQueueTimeoutMS": self.WAIT_QUEUE_TIMEOUT_MS,

            # Timeout Configuration
            "connectTimeoutMS": self.CONNECTION_TIMEOUT_MS,
            "serverSelectionTimeoutMS": self.SERVER_SELECTION_TIMEOUT_MS,

            # Write Concern: majority for durability
            "w": "majority",
            "journal": True,

            # Read Concern: local for performance
            "readConcernLevel": "local",

            # Read Preference: primaryPreferred (use primary, fallback to secondary)
            "readPreference": "primaryPreferred",

            # Retry writes on network errors
            "retryWrites": True,
            "retryReads": True,

            # Application name for monitoring
            "appName": "building-machinery-chatbot",
        }

    async def connect_async(self) -> AsyncIOMotorClient:
        """
        Create async MongoDB client (for FastAPI)

        Returns:
            AsyncIOMotorClient instance
        """
        if self.client is None:
            try:
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    **self.get_connection_options()
                )
                # Test connection
                await self.client.admin.command('ping')
                logger.info("MongoDB async connection established successfully")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

        return self.client

    def connect_sync(self) -> MongoClient:
        """
        Create sync MongoDB client (for scripts)

        Returns:
            MongoClient instance
        """
        if self.sync_client is None:
            try:
                self.sync_client = MongoClient(
                    self.connection_string,
                    **self.get_connection_options()
                )
                # Test connection
                self.sync_client.admin.command('ping')
                logger.info("MongoDB sync connection established successfully")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

        return self.sync_client

    async def close_async(self):
        """Close async MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("MongoDB async connection closed")

    def close_sync(self):
        """Close sync MongoDB connection"""
        if self.sync_client:
            self.sync_client.close()
            self.sync_client = None
            logger.info("MongoDB sync connection closed")

    def get_database(self, client=None):
        """
        Get database instance

        Args:
            client: MongoDB client (async or sync)

        Returns:
            Database instance
        """
        if client is None:
            client = self.client or self.sync_client

        if client is None:
            raise RuntimeError("No MongoDB client connected")

        return client[self.DATABASE_NAME]


# Global configuration instance
mongodb_config = MongoDBConfig()


async def get_database():
    """
    FastAPI dependency for getting database instance

    Usage:
        @app.get("/endpoint")
        async def endpoint(db = Depends(get_database)):
            ...
    """
    client = await mongodb_config.connect_async()
    return mongodb_config.get_database(client)
