"""
Pinecone Vector Database Service

Handles all operations with Pinecone vector database:
- Query vectors for semantic search
- Upsert vectors with metadata
- Delete vectors by document ID
- Health checks and connection validation
"""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PineconeService:
    """Service for Pinecone vector database operations (sync wrapper for async use)"""

    def __init__(self):
        """Initialize Pinecone client and get index reference"""
        try:
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            # Get index by name - SDK will fetch host automatically
            self.index = self.pc.Index(name=settings.pinecone_index_name)
            logger.info(f"Pinecone client initialized successfully for index: {settings.pinecone_index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {str(e)}")
            raise

    async def query_vectors(
        self,
        embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        namespace: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone index for similar vectors (runs in thread pool)

        Args:
            embedding: Query vector embedding (3072 dimensions for text-embedding-3-large)
            top_k: Number of results to return (default 5)
            filter: Optional metadata filter
            include_metadata: Whether to include metadata in results
            namespace: Optional namespace to query

        Returns:
            List of matches with scores and metadata

        Example:
            results = await pinecone_service.query_vectors(
                embedding=[0.1, 0.2, ...],
                top_k=5,
                filter={"category": "maintenance_manual"}
            )
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            # Run synchronous operation in thread pool
            response = await loop.run_in_executor(
                None,
                lambda: self.index.query(
                    vector=embedding,
                    top_k=top_k,
                    filter=filter,
                    include_metadata=include_metadata,
                    namespace=namespace
                )
            )

            matches = []
            for match in response.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {},
                })

            logger.info(f"Pinecone query returned {len(matches)} matches")
            return matches

        except Exception as e:
            logger.error(f"Pinecone query error: {str(e)}")
            raise

    async def upsert_vectors(
        self,
        vectors: List[tuple[str, List[float], Dict[str, Any]]] | List[Dict[str, Any]],
        namespace: str = "",
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Upsert vectors into Pinecone index (runs in thread pool)

        Args:
            vectors: List of vectors as tuples (id, values, metadata) or dicts
                Example tuples: [
                    ("doc1_chunk0", [0.1, 0.2, ...], {"document_id": "doc1", ...})
                ]
                Example dicts: [
                    {
                        "id": "doc1_chunk0",
                        "values": [0.1, 0.2, ...],
                        "metadata": {"document_id": "doc1", ...}
                    }
                ]
            namespace: Optional namespace for vector isolation
            batch_size: Number of vectors to upsert per batch (default 100)

        Returns:
            Upsert response with count
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            # Run synchronous operation in thread pool
            response = await loop.run_in_executor(
                None,
                lambda: self.index.upsert(
                    vectors=vectors,
                    namespace=namespace,
                    batch_size=batch_size
                )
            )

            logger.info(f"Upserted {response.upserted_count} vectors to Pinecone")
            return {"upserted_count": response.upserted_count}

        except Exception as e:
            logger.error(f"Pinecone upsert error: {str(e)}")
            raise

    async def delete_vectors_by_filter(
        self,
        filter: Dict[str, Any],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Delete vectors by metadata filter (runs in thread pool)

        Args:
            filter: Metadata filter to identify vectors to delete
                Example: {"document_id": "doc123"}
            namespace: Optional namespace

        Returns:
            Deletion response
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                lambda: self.index.delete(filter=filter, namespace=namespace)
            )

            logger.info(f"Deleted vectors matching filter: {filter}")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Pinecone delete error: {str(e)}")
            raise

    async def delete_vectors_by_ids(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Delete vectors by IDs (runs in thread pool)

        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace

        Returns:
            Deletion response
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                lambda: self.index.delete(ids=ids, namespace=namespace)
            )

            logger.info(f"Deleted {len(ids)} vectors by ID")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Pinecone delete error: {str(e)}")
            raise

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics (runs in thread pool)

        Returns:
            Index statistics including vector count
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            stats = await loop.run_in_executor(
                None,
                lambda: self.index.describe_index_stats()
            )

            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "namespaces": stats.namespaces
            }

        except Exception as e:
            logger.error(f"Pinecone stats error: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Pinecone service health

        Returns:
            Health status with connection info
        """
        try:
            # Try to get index stats as health check
            stats = await self.get_index_stats()

            return {
                "status": "healthy",
                "connected": True,
                "index_name": settings.pinecone_index_name,
                "vector_count": stats["total_vector_count"]
            }

        except Exception as e:
            logger.error(f"Pinecone health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Singleton instance
_pinecone_service = None


def get_pinecone_service() -> PineconeService:
    """Get singleton Pinecone service instance"""
    global _pinecone_service
    if _pinecone_service is None:
        _pinecone_service = PineconeService()
    return _pinecone_service


# Standalone functions for direct imports (used by tests)
def query_vectors(
    embedding: List[float],
    top_k: int = 5,
    filter: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True,
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Query Pinecone index for similar vectors (synchronous wrapper).

    Args:
        embedding: Query vector embedding
        top_k: Number of results to return
        filter: Optional metadata filter
        include_metadata: Whether to include metadata in results
        namespace: Optional namespace to query

    Returns:
        Dictionary with matches list

    Note:
        This is a synchronous wrapper for testing.
    """
    import asyncio
    service = get_pinecone_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    matches = loop.run_until_complete(
        service.query_vectors(embedding, top_k=top_k, filter=filter, include_metadata=include_metadata, namespace=namespace)
    )

    return {"matches": matches}


def upsert_vectors(
    vectors: List[tuple[str, List[float], Dict[str, Any]]] | List[Dict[str, Any]],
    namespace: str = "",
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Upsert vectors into Pinecone index (synchronous wrapper).

    Args:
        vectors: List of vectors as tuples (id, values, metadata) or dicts
        namespace: Optional namespace for vector isolation
        batch_size: Number of vectors to upsert per batch

    Returns:
        Dictionary with upserted_count
    """
    import asyncio
    service = get_pinecone_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        service.upsert_vectors(vectors, namespace=namespace, batch_size=batch_size)
    )


def delete_vectors_by_filter(
    filter: Dict[str, Any],
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Delete vectors by metadata filter (synchronous wrapper).

    Args:
        filter: Metadata filter to identify vectors to delete
        namespace: Optional namespace

    Returns:
        Deletion response
    """
    import asyncio
    service = get_pinecone_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        service.delete_vectors_by_filter(filter, namespace=namespace)
    )


def delete_vectors_by_ids(
    ids: List[str],
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Delete vectors by IDs (synchronous wrapper).

    Args:
        ids: List of vector IDs to delete
        namespace: Optional namespace

    Returns:
        Deletion response
    """
    import asyncio
    service = get_pinecone_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        service.delete_vectors_by_ids(ids, namespace=namespace)
    )
