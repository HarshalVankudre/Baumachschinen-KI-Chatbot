"""
Pinecone Vector Database Configuration
Handles index configuration, metadata schema, and connection management
"""

import os
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PineconeConfig:
    """Pinecone vector database configuration"""

    # Index Configuration (DB-015)
    INDEX_NAME = "building-machinery-docs"
    DIMENSION = 3072  # text-embedding-3-large
    METRIC = "cosine"  # Cosine similarity for text embeddings
    POD_TYPE = "p1.x1"  # Suitable for 40-50 users, ~100K vectors
    REPLICAS = 1  # No replication for cost optimization
    REGION = "us-east-1"  # Same as MongoDB and Digital Ocean

    # Query Configuration (DB-019)
    DEFAULT_TOP_K = 5  # Retrieve top 5 most relevant chunks
    RELEVANCE_THRESHOLD = 0.7  # Minimum similarity score

    # Batch Configuration (DB-018)
    UPSERT_BATCH_SIZE = 100  # Vectors per batch

    # Metadata Schema (DB-016)
    METADATA_SCHEMA = {
        "document_id": "string",  # UUID from MongoDB
        "filename": "string",
        "category": "string",
        "upload_date": "string",  # ISO8601 datetime
        "uploader_name": "string",
        "chunk_index": "integer",
        "total_chunks": "integer",
        "text_content": "string"  # Original text (optional in prod)
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pinecone configuration

        Args:
            api_key: Pinecone API key
                    If None, reads from PINECONE_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("Pinecone API key not provided")

        self.index = None

    def get_index_config(self) -> Dict[str, Any]:
        """
        Get index configuration for creation

        Returns:
            Dictionary of index configuration
        """
        return {
            "name": self.INDEX_NAME,
            "dimension": self.DIMENSION,
            "metric": self.METRIC,
            "pod_type": self.POD_TYPE,
            "replicas": self.REPLICAS,
            "metadata_config": {
                "indexed": ["document_id", "category", "upload_date"]
            }
        }

    @staticmethod
    def create_vector_id(document_id: str, chunk_index: int) -> str:
        """
        Create Pinecone vector ID

        Args:
            document_id: MongoDB document ID
            chunk_index: Chunk index (0-based)

        Returns:
            Vector ID: {document_id}_{chunk_index}
        """
        return f"{document_id}_{chunk_index}"

    @staticmethod
    def create_metadata(
        document_id: str,
        filename: str,
        category: str,
        upload_date: datetime,
        uploader_name: str,
        chunk_index: int,
        total_chunks: int,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create metadata dictionary for vector

        Args:
            document_id: MongoDB document ID
            filename: Original filename
            category: Document category
            upload_date: Upload datetime
            uploader_name: User who uploaded
            chunk_index: Chunk position (0-based)
            total_chunks: Total chunks in document
            text_content: Original text (optional)

        Returns:
            Metadata dictionary
        """
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "category": category,
            "upload_date": upload_date.isoformat(),
            "uploader_name": uploader_name,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks
        }

        # Add text_content only if provided (for debugging)
        if text_content:
            metadata["text_content"] = text_content

        return metadata

    @staticmethod
    def create_query_filter(
        document_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create metadata filter for queries

        Args:
            document_id: Filter by specific document
            category: Filter by category
            start_date: Filter by upload date >= start_date
            end_date: Filter by upload date <= end_date

        Returns:
            Filter dictionary or None
        """
        filters = {}

        if document_id:
            filters["document_id"] = {"$eq": document_id}

        if category:
            filters["category"] = {"$eq": category}

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date.isoformat()
            if end_date:
                date_filter["$lte"] = end_date.isoformat()
            filters["upload_date"] = date_filter

        return filters if filters else None


# Global configuration instance
pinecone_config = PineconeConfig()
