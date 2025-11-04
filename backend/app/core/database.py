"""
MongoDB database connection and management.
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

from app.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Connect to MongoDB and initialize database."""
    global _mongo_client, _mongo_db

    try:
        logger.info(f"Connecting to MongoDB: {settings.mongodb_database}")

        _mongo_client = AsyncIOMotorClient(
            settings.mongodb_uri,
            minPoolSize=settings.mongodb_min_pool_size,
            maxPoolSize=settings.mongodb_max_pool_size,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
        )

        # Verify connection
        await _mongo_client.admin.command("ping")

        _mongo_db = _mongo_client[settings.mongodb_database]

        logger.info("MongoDB connected successfully")

        # Create indexes
        await create_indexes()

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if _mongo_db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _mongo_db


async def create_indexes() -> None:
    """Create database indexes for performance."""
    db = get_database()

    logger.info("Creating MongoDB indexes...")

    try:
        # Users collection indexes
        await db.users.create_index([("username", ASCENDING)], unique=True)
        await db.users.create_index([("email", ASCENDING)], unique=True)
        await db.users.create_index([("account_status", ASCENDING)])
        await db.users.create_index([("email_verification_token", ASCENDING)])

        # Sessions collection indexes
        await db.sessions.create_index([("session_id", ASCENDING)], unique=True)
        await db.sessions.create_index([("user_id", ASCENDING)])
        await db.sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

        # Conversations collection indexes
        await db.conversations.create_index([("conversation_id", ASCENDING)], unique=True)
        await db.conversations.create_index([("user_id", ASCENDING)])
        await db.conversations.create_index([("last_message_at", DESCENDING)])
        await db.conversations.create_index([("user_id", ASCENDING), ("deleted", ASCENDING)])

        # Document metadata collection indexes
        await db.document_metadata.create_index([("document_id", ASCENDING)], unique=True)
        await db.document_metadata.create_index([("uploader_id", ASCENDING)])
        await db.document_metadata.create_index([("category", ASCENDING)])
        await db.document_metadata.create_index([("upload_date", DESCENDING)])
        await db.document_metadata.create_index([("processing_status", ASCENDING)])
        await db.document_metadata.create_index([("deleted", ASCENDING)])

        # Compound indexes for optimized queries in list_documents endpoint
        # This index supports the common query pattern: deleted + category + upload_date sort
        await db.document_metadata.create_index([
            ("deleted", ASCENDING),
            ("category", ASCENDING),
            ("upload_date", DESCENDING)
        ])

        # This index supports filename search with deleted filter
        await db.document_metadata.create_index([
            ("deleted", ASCENDING),
            ("filename", ASCENDING)
        ])

        # This index supports uploader filter with deleted and upload_date sort
        await db.document_metadata.create_index([
            ("deleted", ASCENDING),
            ("uploader_name", ASCENDING),
            ("upload_date", DESCENDING)
        ])

        # Audit logs collection indexes
        await db.audit_logs.create_index([("log_id", ASCENDING)], unique=True)
        await db.audit_logs.create_index([("timestamp", DESCENDING)])
        await db.audit_logs.create_index([("admin_user_id", ASCENDING)])
        await db.audit_logs.create_index([("action_type", ASCENDING)])
        await db.audit_logs.create_index([("target_user_id", ASCENDING)])

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        # Don't raise - indexes are optimization, not critical for startup


async def health_check() -> bool:
    """Check MongoDB connection health."""
    try:
        if _mongo_client is None:
            return False

        await _mongo_client.admin.command("ping")
        return True
    except Exception:
        return False
