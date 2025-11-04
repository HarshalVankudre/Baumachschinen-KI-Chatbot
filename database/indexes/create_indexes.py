"""
Create All MongoDB Indexes
Implements indexing strategy for all collections (DB-004, DB-006, DB-008, DB-010)
"""

import logging
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from typing import List

logger = logging.getLogger(__name__)


class MongoDBIndexes:
    """MongoDB index creation and management"""

    @staticmethod
    def get_users_indexes() -> List[IndexModel]:
        """
        Get index definitions for users collection (DB-004)

        Returns:
            List of IndexModel objects
        """
        return [
            # 1. Unique index on user_id
            IndexModel(
                [("user_id", ASCENDING)],
                name="idx_user_id",
                unique=True
            ),

            # 2. Unique index on username
            IndexModel(
                [("username", ASCENDING)],
                name="idx_username",
                unique=True
            ),

            # 3. Unique index on email
            IndexModel(
                [("email", ASCENDING)],
                name="idx_email",
                unique=True
            ),

            # 4. Index on account_status (for filtering pending approvals)
            IndexModel(
                [("account_status", ASCENDING)],
                name="idx_account_status"
            ),

            # 5. Index on created_at (for sorting by registration date)
            IndexModel(
                [("created_at", DESCENDING)],
                name="idx_created_at"
            ),

            # 6. Compound index on account_status and email_verified
            IndexModel(
                [
                    ("account_status", ASCENDING),
                    ("email_verified", ASCENDING)
                ],
                name="idx_account_status_email_verified"
            ),

            # 7. Sparse index on email_verification_token
            IndexModel(
                [("email_verification_token", ASCENDING)],
                name="idx_email_verification_token",
                sparse=True
            )
        ]

    @staticmethod
    def get_conversations_indexes() -> List[IndexModel]:
        """
        Get index definitions for conversations collection (DB-006)

        Returns:
            List of IndexModel objects
        """
        return [
            # 1. Unique index on conversation_id
            IndexModel(
                [("conversation_id", ASCENDING)],
                name="idx_conversation_id",
                unique=True
            ),

            # 2. Compound index on user_id and updated_at
            # (list user's conversations sorted by recent activity)
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("updated_at", DESCENDING)
                ],
                name="idx_user_updated"
            ),

            # 3. Text index on messages.content and title
            IndexModel(
                [
                    ("messages.content", TEXT),
                    ("title", TEXT)
                ],
                name="conversation_search",
                weights={
                    "title": 10,
                    "messages.content": 5
                },
                default_language="english"
            ),

            # 4. Index on user_id and created_at
            # (alternative sorting, analytics)
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("created_at", DESCENDING)
                ],
                name="idx_user_created"
            )
        ]

    @staticmethod
    def get_audit_logs_indexes() -> List[IndexModel]:
        """
        Get index definitions for audit_logs collection (DB-008)

        Returns:
            List of IndexModel objects
        """
        return [
            # 1. Unique index on log_id
            IndexModel(
                [("log_id", ASCENDING)],
                name="idx_log_id",
                unique=True
            ),

            # 2. Index on timestamp (sort logs by recency)
            IndexModel(
                [("timestamp", DESCENDING)],
                name="idx_timestamp"
            ),

            # 3. Index on admin_user_id (filter logs by admin)
            IndexModel(
                [("admin_user_id", ASCENDING)],
                name="idx_admin_user_id"
            ),

            # 4. Index on action_type (filter logs by action)
            IndexModel(
                [("action_type", ASCENDING)],
                name="idx_action_type"
            ),

            # 5. Compound index on action_type and timestamp
            IndexModel(
                [
                    ("action_type", ASCENDING),
                    ("timestamp", DESCENDING)
                ],
                name="idx_action_timestamp"
            ),

            # 6. Compound index for date range queries
            IndexModel(
                [
                    ("timestamp", ASCENDING),
                    ("admin_user_id", ASCENDING)
                ],
                name="idx_timestamp_admin"
            )
        ]

    @staticmethod
    def get_document_metadata_indexes() -> List[IndexModel]:
        """
        Get index definitions for document_metadata collection (DB-010)

        Returns:
            List of IndexModel objects
        """
        return [
            # 1. Unique index on document_id
            IndexModel(
                [("document_id", ASCENDING)],
                name="idx_document_id",
                unique=True
            ),

            # 2. Index on uploader_user_id (filter by uploader)
            IndexModel(
                [("uploader_user_id", ASCENDING)],
                name="idx_uploader_user_id"
            ),

            # 3. Index on category (filter by category)
            IndexModel(
                [("category", ASCENDING)],
                name="idx_category"
            ),

            # 4. Index on upload_date (sort by recency)
            IndexModel(
                [("upload_date", DESCENDING)],
                name="idx_upload_date"
            ),

            # 5. Index on deleted (exclude deleted documents)
            IndexModel(
                [("deleted", ASCENDING)],
                name="idx_deleted"
            ),

            # 6. Compound index on deleted and upload_date
            # (efficiently list active documents sorted by date)
            IndexModel(
                [
                    ("deleted", ASCENDING),
                    ("upload_date", DESCENDING)
                ],
                name="idx_deleted_upload_date"
            ),

            # 7. Text index on filename (search by filename)
            IndexModel(
                [("filename", TEXT)],
                name="filename_search",
                default_language="english"
            )
        ]


def create_all_indexes(db):
    """
    Create all indexes for all collections

    Args:
        db: MongoDB database instance

    Returns:
        Dictionary with creation results
    """
    results = {}
    indexes = MongoDBIndexes()

    collections = {
        "users": indexes.get_users_indexes(),
        "conversations": indexes.get_conversations_indexes(),
        "audit_logs": indexes.get_audit_logs_indexes(),
        "document_metadata": indexes.get_document_metadata_indexes()
    }

    for collection_name, index_models in collections.items():
        try:
            collection = db[collection_name]
            index_names = collection.create_indexes(index_models)
            results[collection_name] = {
                "status": "success",
                "indexes_created": index_names
            }
            logger.info(
                f"Created {len(index_names)} indexes for {collection_name}: {index_names}"
            )
        except Exception as e:
            results[collection_name] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"Failed to create indexes for {collection_name}: {e}")

    return results


def verify_indexes(db):
    """
    Verify that all indexes exist

    Args:
        db: MongoDB database instance

    Returns:
        Dictionary with verification results
    """
    results = {}
    collection_names = ["users", "conversations", "audit_logs", "document_metadata"]

    for collection_name in collection_names:
        try:
            collection = db[collection_name]
            indexes = list(collection.list_indexes())
            index_names = [idx["name"] for idx in indexes]

            results[collection_name] = {
                "status": "success",
                "index_count": len(indexes),
                "indexes": index_names
            }
            logger.info(
                f"Verified {len(indexes)} indexes for {collection_name}"
            )
        except Exception as e:
            results[collection_name] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"Failed to verify indexes for {collection_name}: {e}")

    return results


if __name__ == "__main__":
    # For standalone execution
    from database.config.mongodb_config import MongoDBConfig

    logging.basicConfig(level=logging.INFO)

    # Connect to MongoDB
    config = MongoDBConfig()
    client = config.connect_sync()
    db = config.get_database(client)

    print("\nCreating indexes...")
    results = create_all_indexes(db)

    print("\nResults:")
    for collection, result in results.items():
        if result["status"] == "success":
            print(f"✓ {collection}: {len(result['indexes_created'])} indexes created")
        else:
            print(f"✗ {collection}: {result['error']}")

    print("\nVerifying indexes...")
    verify_results = verify_indexes(db)

    print("\nVerification:")
    for collection, result in verify_results.items():
        if result["status"] == "success":
            print(f"✓ {collection}: {result['index_count']} indexes")
        else:
            print(f"✗ {collection}: {result['error']}")

    config.close_sync()
