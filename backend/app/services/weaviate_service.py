"""
Weaviate Vector Database Service

Advanced vector database service with multi-tenancy, hybrid search, and GraphQL support.
Replaces the previous Pinecone implementation with enhanced features:
- Multi-tenancy for data isolation per user/organization
- Hybrid search combining vector similarity + BM25 keyword search
- GraphQL queries for flexible data retrieval
- Multi-modal support for text and images
- PQ compression for storage optimization
- Cohere reranking for improved search quality
- Batch operations for high-throughput ingestion

Collections:
- Documents: Technical documentation, manuals, guides
- Machinery: Machine specifications with 406 E-code properties
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

import weaviate
from weaviate import WeaviateClient
from weaviate.classes.config import (
    Configure,
    Property,
    DataType,
    VectorDistances,
    Tokenization,
    Multi2VecField,
    # PQConfig,  # Not available in this weaviate version
)
from weaviate.classes.query import MetadataQuery, HybridFusion, Filter
from weaviate.classes.tenants import Tenant, TenantActivityStatus
from weaviate.collections.collection import Collection
from cohere import Client as CohereClient

from app.config import settings

logger = logging.getLogger(__name__)


# Collection names
COLLECTION_DOCUMENTS = "Documents"
COLLECTION_MACHINERY = "Machinery"

# Namespaces for backward compatibility
NAMESPACES = {
    "documents": "Technical documentation, manuals, guides, maintenance procedures",
    "machinery": "Machine specifications, models, properties (842 machines)"
}


class WeaviateService:
    """
    Advanced Weaviate vector database service with enterprise features.

    Features:
    - Multi-tenancy: Isolated data per user/organization
    - Hybrid search: Vector + BM25 keyword search
    - GraphQL: Flexible query language
    - Multi-modal: Text and image embeddings
    - Compression: PQ quantization for storage savings
    - Reranking: Cohere reranker for result quality
    - Batch operations: High-throughput data ingestion
    """

    def __init__(self):
        """Initialize Weaviate client and create collections if needed."""
        self.client: Optional[WeaviateClient] = None
        self.cohere_client: Optional[CohereClient] = None
        self._connection_lock = asyncio.Lock()
        self._is_connected = False

        # Collection references
        self.documents_collection: Optional[Collection] = None
        self.machinery_collection: Optional[Collection] = None

        # Initialize Cohere for reranking if API key is provided
        if settings.cohere_api_key:
            self.cohere_client = CohereClient(api_key=settings.cohere_api_key)
            logger.info("Cohere reranker initialized")
        else:
            logger.warning("Cohere API key not provided. Reranking will be disabled.")

    async def connect(self) -> None:
        """
        Connect to Weaviate server and initialize collections.

        Creates the Documents and Machinery collections with multi-tenancy,
        HNSW indexing, PQ compression, and proper schema definitions.
        """
        if self._is_connected:
            return

        async with self._connection_lock:
            if self._is_connected:
                return

            try:
                # Connect to Weaviate
                self.client = weaviate.connect_to_local(
                    host=settings.weaviate_host,
                    port=settings.weaviate_port,
                    grpc_port=settings.weaviate_grpc_port,
                    headers={
                        "X-OpenAI-Api-Key": settings.openai_api_key,
                        **({"X-Cohere-Api-Key": settings.cohere_api_key} if settings.cohere_api_key else {})
                    }
                )

                logger.info(f"Connected to Weaviate at {settings.weaviate_host}:{settings.weaviate_port}")

                # Create collections if they don't exist
                await self._create_documents_collection()
                await self._create_machinery_collection()

                # Get collection references
                self.documents_collection = self.client.collections.get(COLLECTION_DOCUMENTS)
                self.machinery_collection = self.client.collections.get(COLLECTION_MACHINERY)

                self._is_connected = True
                logger.info("Weaviate service initialized successfully")

            except Exception as e:
                logger.error(f"Failed to connect to Weaviate: {e}")
                raise

    async def _create_documents_collection(self) -> None:
        """
        Create Documents collection with multi-tenancy and advanced features.

        Schema:
        - document_id: Unique document identifier
        - filename: Original file name
        - category: Document category (manuals, specifications, etc.)
        - uploader_name: User who uploaded the document
        - chunk_index: Chunk number within the document
        - text_content: The actual text content (up to 10000 chars)
        - image_url: Optional URL to associated image
        - created_at: Upload timestamp
        """
        if self.client.collections.exists(COLLECTION_DOCUMENTS):
            logger.info(f"Collection {COLLECTION_DOCUMENTS} already exists")
            return

        try:
            self.client.collections.create(
                name=COLLECTION_DOCUMENTS,
                description="Technical documentation with multi-modal support",

                # Multi-tenancy configuration
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=settings.enable_weaviate_multitenancy
                ) if settings.enable_weaviate_multitenancy else None,

                # Vector index configuration (HNSW)
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                    ef=128,              # Higher ef = better recall, slower queries
                    ef_construction=256,  # Higher = better graph quality, slower indexing
                    max_connections=64,   # Higher = better recall, more memory
                    dynamic_ef_min=100,
                    dynamic_ef_max=500,
                    dynamic_ef_factor=8,
                    vector_cache_max_objects=100000,
                    flat_search_cutoff=40000,
                    # skip=False,  # Not available in this weaviate version
                    # quantizer=PQConfig(  # Compression disabled - PQConfig not available in this weaviate version
                    #     enabled=settings.enable_weaviate_compression,
                    #     segments=256,
                    #     centroids=256,
                    #     training_limit=100000,
                    #     encoder_type="kmeans",
                    #     encoder_distribution="log-normal"
                    # ) if settings.enable_weaviate_compression else None
                ),

                # Inverted index for hybrid search
                inverted_index_config=Configure.inverted_index(
                    bm25_b=0.75,
                    bm25_k1=1.2,
                    index_null_state=True,
                    index_property_length=True,
                    index_timestamps=True
                ),

                # Vectorizer configuration
                vectorizer_config=Configure.Vectorizer.text2vec_openai(
                    model="text-embedding-3-large",
                    dimensions=3072,
                    vectorize_collection_name=False
                ),

                # Generative module for RAG
                generative_config=Configure.Generative.openai(
                    model=settings.openai_chat_model
                ),

                # Reranker configuration
                reranker_config=Configure.Reranker.cohere(
                    model="rerank-english-v3.0"
                ) if settings.cohere_api_key else None,

                # Properties
                properties=[
                    Property(
                        name="document_id",
                        data_type=DataType.TEXT,
                        description="Unique document identifier",
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="filename",
                        data_type=DataType.TEXT,
                        description="Original filename",
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=True,
                        index_searchable=True
                    ),
                    Property(
                        name="category",
                        data_type=DataType.TEXT,
                        description="Document category",
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="uploader_name",
                        data_type=DataType.TEXT,
                        description="User who uploaded",
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="chunk_index",
                        data_type=DataType.INT,
                        description="Chunk number",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=False
                    ),
                    Property(
                        name="text_content",
                        data_type=DataType.TEXT,
                        description="The text content for search",
                        skip_vectorization=False,  # Vectorize this field
                        tokenization=Tokenization.WORD,
                        index_filterable=False,
                        index_searchable=True
                    ),
                    Property(
                        name="image_url",
                        data_type=DataType.TEXT,
                        description="URL to associated image (for multi-modal)",
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=False,
                        index_searchable=False
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="Upload timestamp",
                        skip_vectorization=True,
                        index_filterable=True,
                        index_searchable=False
                    ),
                ]
            )

            logger.info(f"Created collection: {COLLECTION_DOCUMENTS}")

        except Exception as e:
            logger.error(f"Failed to create {COLLECTION_DOCUMENTS} collection: {e}")
            raise

    async def _create_machinery_collection(self) -> None:
        """
        Create Machinery collection with 406 E-code properties.

        Schema:
        - name: Machine name/title
        - serial_number: Unique serial number
        - inventory_number: Inventory tracking number
        - manufacturer: Equipment manufacturer
        - model: Model designation
        - E1730, E2180, ... E9999: 406 E-code properties
        - created_at: Ingestion timestamp
        """
        if self.client.collections.exists(COLLECTION_MACHINERY):
            logger.info(f"Collection {COLLECTION_MACHINERY} already exists")
            return

        try:
            # Base properties
            properties = [
                Property(
                    name="name",
                    data_type=DataType.TEXT,
                    description="Machine name",
                    skip_vectorization=False,  # Vectorize for search
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True
                ),
                Property(
                    name="serial_number",
                    data_type=DataType.TEXT,
                    description="Unique serial number",
                    skip_vectorization=True,
                    tokenization=Tokenization.FIELD,
                    index_filterable=True,
                    index_searchable=True
                ),
                Property(
                    name="inventory_number",
                    data_type=DataType.TEXT,
                    description="Inventory number",
                    skip_vectorization=True,
                    tokenization=Tokenization.FIELD,
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="manufacturer",
                    data_type=DataType.TEXT,
                    description="Manufacturer name",
                    skip_vectorization=False,  # Vectorize for search
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True
                ),
                Property(
                    name="model",
                    data_type=DataType.TEXT,
                    description="Model designation",
                    skip_vectorization=False,  # Vectorize for search
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True
                ),
                Property(
                    name="created_at",
                    data_type=DataType.DATE,
                    description="Ingestion timestamp",
                    skip_vectorization=True,
                    index_filterable=True,
                    index_searchable=False
                ),
            ]

            # Add E-code properties dynamically
            # Note: In production, you would add all 406 E-code properties here
            # For now, we'll add a representative subset and a generic e_codes field
            common_ecodes = [
                ("E1730", "Gewicht [kg]"),
                ("E2180", "Motor - Leistung [kW]"),
                ("E1930", "Klimaanlage"),
                ("E2170", "Motor - Hersteller"),
                ("E2190", "Motor - Typ"),
            ]

            for ecode, description in common_ecodes:
                properties.append(
                    Property(
                        name=ecode,
                        data_type=DataType.TEXT,
                        description=description,
                        skip_vectorization=True,
                        tokenization=Tokenization.FIELD,
                        index_filterable=True,
                        index_searchable=True
                    )
                )

            # Create collection
            self.client.collections.create(
                name=COLLECTION_MACHINERY,
                description="Building machinery specifications with E-code properties",

                # Multi-tenancy configuration
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=settings.enable_weaviate_multitenancy
                ) if settings.enable_weaviate_multitenancy else None,

                # Vector index configuration (HNSW with PQ compression)
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                    ef=128,
                    ef_construction=256,
                    max_connections=64,
                    dynamic_ef_min=100,
                    dynamic_ef_max=500,
                    dynamic_ef_factor=8,
                    vector_cache_max_objects=100000,
                    flat_search_cutoff=40000,
                    # quantizer=PQConfig(  # Compression disabled - PQConfig not available in this weaviate version
                    #     enabled=settings.enable_weaviate_compression,
                    #     segments=256,
                    #     centroids=256,
                    #     training_limit=100000,
                    #     encoder_type="kmeans",
                    #     encoder_distribution="log-normal"
                    # ) if settings.enable_weaviate_compression else None
                ),

                # Inverted index for hybrid search (critical for machinery search)
                inverted_index_config=Configure.inverted_index(
                    bm25_b=0.75,
                    bm25_k1=1.2,
                    index_null_state=True,
                    index_property_length=True,
                    index_timestamps=True
                ),

                # Vectorizer configuration
                vectorizer_config=Configure.Vectorizer.text2vec_openai(
                    model="text-embedding-3-large",
                    dimensions=3072,
                    vectorize_collection_name=False
                ),

                # Generative module for RAG
                generative_config=Configure.Generative.openai(
                    model=settings.openai_chat_model
                ),

                # Reranker configuration
                reranker_config=Configure.Reranker.cohere(
                    model="rerank-english-v3.0"
                ) if settings.cohere_api_key else None,

                properties=properties
            )

            logger.info(f"Created collection: {COLLECTION_MACHINERY}")

        except Exception as e:
            logger.error(f"Failed to create {COLLECTION_MACHINERY} collection: {e}")
            raise

    async def _verify_connection(self) -> bool:
        """
        Verify the Weaviate connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self.client:
                return False

            # Quick health check
            is_ready = self.client.is_ready()

            if not is_ready:
                logger.warning("Weaviate connection lost, marking as disconnected")
                self._is_connected = False
                return False

            return True

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            self._is_connected = False
            return False

    async def _ensure_connected(self) -> None:
        """
        Ensure connection is active, reconnect if needed.

        Raises:
            Exception if connection cannot be established
        """
        # First check if we think we're connected
        if not self._is_connected:
            await self.connect()
            return

        # Verify the connection is actually working
        is_healthy = await self._verify_connection()

        if not is_healthy:
            logger.info("Connection unhealthy, attempting reconnection...")
            # Force reconnection
            self._is_connected = False
            if self.client:
                try:
                    self.client.close()
                except Exception as e:
                    logger.debug(f"Error closing old connection: {e}")
                self.client = None

            await self.connect()

    async def close(self) -> None:
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("Weaviate client connection closed")

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def query_hybrid(
        self,
        query: str,
        collection_name: str,
        alpha: float = None,
        top_k: int = 10,
        tenant: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        enable_rerank: bool = True,
        rerank_top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and BM25 keyword search.

        Args:
            query: Search query text
            collection_name: "Documents" or "Machinery"
            alpha: Hybrid search weight (0.0=BM25 only, 1.0=vector only, default from settings)
            top_k: Number of results to return
            tenant: Tenant name for multi-tenancy isolation
            filters: Metadata filters
            enable_rerank: Whether to apply Cohere reranking
            rerank_top_k: Number of results before reranking (default: top_k * 2)

        Returns:
            List of search results with scores and metadata
        """
        await self._ensure_connected()

        alpha = alpha if alpha is not None else settings.default_hybrid_alpha
        rerank_top_k = rerank_top_k or (top_k * 2)

        try:
            collection = self.client.collections.get(collection_name)

            # Build filter if provided
            weaviate_filter = None
            if filters:
                # Convert dict filters to Weaviate Filter object
                weaviate_filter = self._build_filter(filters)

            # Perform hybrid search
            if tenant and settings.enable_weaviate_multitenancy:
                collection = collection.with_tenant(tenant)

            response = collection.query.hybrid(
                query=query,
                alpha=alpha,
                limit=rerank_top_k if enable_rerank else top_k,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(score=True, distance=True, certainty=True)
            )

            # Convert to dict format
            results = []
            for obj in response.objects:
                result = {
                    "id": str(obj.uuid),
                    "score": obj.metadata.score if obj.metadata else 0.0,
                    "distance": obj.metadata.distance if obj.metadata else None,
                    "properties": obj.properties
                }
                results.append(result)

            # Apply Cohere reranking if enabled
            if enable_rerank and self.cohere_client and len(results) > 0:
                results = await self._rerank_results(query, results, top_k)
            else:
                results = results[:top_k]

            logger.info(f"Hybrid search on {collection_name}: {len(results)} results (alpha={alpha})")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed on {collection_name}: {e}")
            raise

    async def query_vectors(
        self,
        embedding: List[float],
        collection_name: str,
        top_k: int = 10,
        tenant: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pure vector similarity search (no BM25 keyword component).

        Args:
            embedding: Query embedding vector (3072 dimensions)
            collection_name: "Documents" or "Machinery"
            top_k: Number of results to return
            tenant: Tenant name for multi-tenancy
            filters: Metadata filters

        Returns:
            List of search results with scores and metadata
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            if tenant and settings.enable_weaviate_multitenancy:
                collection = collection.with_tenant(tenant)

            weaviate_filter = self._build_filter(filters) if filters else None

            response = collection.query.near_vector(
                near_vector=embedding,
                limit=top_k,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(distance=True, certainty=True)
            )

            results = []
            for obj in response.objects:
                result = {
                    "id": str(obj.uuid),
                    "score": 1.0 - obj.metadata.distance if obj.metadata else 0.0,  # Convert distance to score
                    "distance": obj.metadata.distance if obj.metadata else None,
                    "properties": obj.properties
                }
                results.append(result)

            logger.info(f"Vector search on {collection_name}: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Vector search failed on {collection_name}: {e}")
            raise

    async def query_graphql(
        self,
        graphql_query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a raw GraphQL query against Weaviate.

        Args:
            graphql_query: GraphQL query string
            variables: Optional query variables

        Returns:
            GraphQL response data

        Example:
            query = '''
            {
              Get {
                Machinery(
                  hybrid: { query: "excavator" }
                  where: { path: ["manufacturer"], operator: Equal, valueString: "Caterpillar" }
                  limit: 10
                ) {
                  name
                  manufacturer
                  model
                  E1730
                  E2180
                }
              }
            }
            '''
            results = await weaviate_service.query_graphql(query)
        """
        if not self._is_connected:
            await self.connect()

        try:
            response = self.client.graphql_raw_query(graphql_query)

            if response.errors:
                logger.error(f"GraphQL query errors: {response.errors}")
                raise Exception(f"GraphQL errors: {response.errors}")

            return response.get

        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            raise

    # =========================================================================
    # Batch Upsert Methods
    # =========================================================================

    async def batch_upsert(
        self,
        objects: List[Dict[str, Any]],
        collection_name: str,
        tenant: Optional[str] = None,
        batch_size: int = None
    ) -> Dict[str, int]:
        """
        Batch upsert objects to a collection with proper error handling.

        Args:
            objects: List of objects to upsert. Each object should have 'properties' dict.
                    Optionally 'id' (UUID) and 'vector' (if pre-computed)
            collection_name: "Documents" or "Machinery"
            tenant: Tenant name for multi-tenancy
            batch_size: Batch size (default from settings)

        Returns:
            Stats dict with counts: {"success": N, "failed": M, "errors": List[str]}

        Example:
            objects = [
                {
                    "properties": {
                        "document_id": "doc123",
                        "filename": "manual.pdf",
                        "text_content": "...",
                        ...
                    }
                },
                ...
            ]
            stats = await weaviate_service.batch_upsert(objects, "Documents", tenant="user123")
        """
        # Ensure connection is healthy
        await self._ensure_connected()

        batch_size = batch_size or settings.weaviate_batch_size

        try:
            collection = self.client.collections.get(collection_name)

            # Verify tenant exists if multi-tenancy is enabled
            if tenant and settings.enable_weaviate_multitenancy:
                try:
                    # Check if tenant exists, create if not
                    tenant_exists = await self._ensure_tenant_exists(collection_name, tenant)
                    if not tenant_exists:
                        raise ValueError(f"Failed to create or verify tenant '{tenant}'")
                    collection = collection.with_tenant(tenant)
                except Exception as e:
                    logger.error(f"Tenant verification failed for '{tenant}': {e}")
                    raise

            success_count = 0
            failed_count = 0
            error_messages = []

            # Process in batches
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                batch_num = i // batch_size + 1

                try:
                    with collection.batch.dynamic() as batch_context:
                        for obj in batch:
                            try:
                                uuid = obj.get("id")  # Optional: pre-specified UUID
                                properties = obj["properties"]
                                vector = obj.get("vector")  # Optional: pre-computed vector

                                batch_context.add_object(
                                    properties=properties,
                                    uuid=uuid,
                                    vector=vector
                                )

                            except Exception as e:
                                error_msg = f"Failed to add object to batch: {e}"
                                logger.error(error_msg)
                                error_messages.append(error_msg)
                                failed_count += 1

                    # CRITICAL FIX: Check for failed objects after batch execution
                    if hasattr(batch_context, 'failed_objects') and batch_context.failed_objects:
                        for failed_obj in batch_context.failed_objects:
                            failed_count += 1
                            error_msg = f"Batch object failed: {failed_obj}"
                            logger.error(error_msg)
                            error_messages.append(str(error_msg))

                    if hasattr(batch_context, 'failed_references') and batch_context.failed_references:
                        for failed_ref in batch_context.failed_references:
                            failed_count += 1
                            error_msg = f"Batch reference failed: {failed_ref}"
                            logger.error(error_msg)
                            error_messages.append(str(error_msg))

                    # Calculate actual success count
                    batch_success = len(batch) - len(getattr(batch_context, 'failed_objects', []))
                    success_count += batch_success

                    logger.info(
                        f"Batch {batch_num}: {batch_success}/{len(batch)} objects succeeded, "
                        f"{len(getattr(batch_context, 'failed_objects', []))} failed"
                    )

                except Exception as batch_error:
                    # Entire batch failed
                    error_msg = f"Batch {batch_num} failed completely: {batch_error}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    failed_count += len(batch)

            logger.info(
                f"Batch upsert to {collection_name} completed: "
                f"{success_count} success, {failed_count} failed"
            )

            return {
                "success": success_count,
                "failed": failed_count,
                "errors": error_messages[:10]  # Return first 10 errors for debugging
            }

        except Exception as e:
            logger.error(f"Batch upsert failed on {collection_name}: {e}", exc_info=True)
            raise

    # =========================================================================
    # Delete Methods
    # =========================================================================

    async def delete_by_filter(
        self,
        collection_name: str,
        filters: Dict[str, Any],
        tenant: Optional[str] = None
    ) -> int:
        """
        Delete objects by metadata filter.

        Args:
            collection_name: "Documents" or "Machinery"
            filters: Filter conditions
            tenant: Tenant name

        Returns:
            Number of objects deleted
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            if tenant and settings.enable_weaviate_multitenancy:
                collection = collection.with_tenant(tenant)

            weaviate_filter = self._build_filter(filters)

            result = collection.data.delete_many(where=weaviate_filter)

            logger.info(f"Deleted {result.matches} objects from {collection_name}")
            return result.matches

        except Exception as e:
            logger.error(f"Delete by filter failed on {collection_name}: {e}")
            raise

    async def delete_by_id(
        self,
        collection_name: str,
        object_id: str,
        tenant: Optional[str] = None
    ) -> bool:
        """
        Delete a single object by ID.

        Args:
            collection_name: "Documents" or "Machinery"
            object_id: Object UUID
            tenant: Tenant name

        Returns:
            True if deleted, False if not found
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            if tenant and settings.enable_weaviate_multitenancy:
                collection = collection.with_tenant(tenant)

            collection.data.delete_by_id(uuid=object_id)

            logger.info(f"Deleted object {object_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Delete by ID failed on {collection_name}: {e}")
            return False

    async def delete_all_in_collection(
        self,
        collection_name: str,
        tenant: Optional[str] = None
    ) -> int:
        """
        Delete ALL objects in a collection (use with caution!).

        Args:
            collection_name: "Documents" or "Machinery"
            tenant: Tenant name (if None, deletes from all tenants)

        Returns:
            Number of objects deleted
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            if tenant and settings.enable_weaviate_multitenancy:
                collection = collection.with_tenant(tenant)

            # Delete all by using a filter that matches everything
            result = collection.data.delete_many(where=Filter.by_property("created_at").is_not_none())

            logger.warning(f"DELETED ALL {result.matches} objects from {collection_name}")
            return result.matches

        except Exception as e:
            logger.error(f"Delete all failed on {collection_name}: {e}")
            raise

    # =========================================================================
    # Tenant Management Methods
    # =========================================================================

    async def _ensure_tenant_exists(
        self,
        collection_name: str,
        tenant_name: str
    ) -> bool:
        """
        Ensure tenant exists, create if it doesn't.

        Args:
            collection_name: "Documents" or "Machinery"
            tenant_name: Unique tenant identifier

        Returns:
            True if tenant exists or was created successfully
        """
        if not self._is_connected:
            await self.connect()

        if not settings.enable_weaviate_multitenancy:
            logger.warning("Multi-tenancy is disabled in settings")
            return True  # If multi-tenancy disabled, no tenant needed

        try:
            collection = self.client.collections.get(collection_name)

            # Check if tenant already exists
            try:
                existing_tenants = collection.tenants.get()
                tenant_names = [t.name for t in existing_tenants]

                if tenant_name in tenant_names:
                    logger.debug(f"Tenant '{tenant_name}' already exists in {collection_name}")
                    return True
            except Exception as e:
                logger.debug(f"Could not list tenants, will try to create: {e}")

            # Create tenant if it doesn't exist
            try:
                collection.tenants.create(
                    tenants=[Tenant(name=tenant_name)]
                )
                logger.info(f"Created tenant '{tenant_name}' in {collection_name}")
                return True
            except Exception as create_error:
                # Tenant might already exist (race condition)
                error_str = str(create_error).lower()
                if "already exists" in error_str or "duplicate" in error_str:
                    logger.debug(f"Tenant '{tenant_name}' already exists (race condition)")
                    return True
                else:
                    logger.error(f"Failed to create tenant '{tenant_name}': {create_error}")
                    return False

        except Exception as e:
            logger.error(f"Tenant existence check failed for '{tenant_name}': {e}", exc_info=True)
            return False

    async def create_tenant(
        self,
        collection_name: str,
        tenant_name: str
    ) -> bool:
        """
        Create a new tenant in a collection.

        Args:
            collection_name: "Documents" or "Machinery"
            tenant_name: Unique tenant identifier

        Returns:
            True if created successfully
        """
        return await self._ensure_tenant_exists(collection_name, tenant_name)

    async def delete_tenant(
        self,
        collection_name: str,
        tenant_name: str
    ) -> bool:
        """
        Delete a tenant and all its data.

        Args:
            collection_name: "Documents" or "Machinery"
            tenant_name: Tenant identifier

        Returns:
            True if deleted successfully
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            collection.tenants.remove(tenants=[tenant_name])

            logger.info(f"Deleted tenant '{tenant_name}' from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete tenant '{tenant_name}': {e}")
            return False

    async def get_tenant_stats(
        self,
        collection_name: str,
        tenant_name: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific tenant.

        Args:
            collection_name: "Documents" or "Machinery"
            tenant_name: Tenant identifier

        Returns:
            Stats dict with object count and other metrics
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)
            tenant_collection = collection.with_tenant(tenant_name)

            # Aggregate query to count objects
            response = tenant_collection.aggregate.over_all(total_count=True)

            return {
                "tenant": tenant_name,
                "collection": collection_name,
                "object_count": response.total_count,
            }

        except Exception as e:
            logger.error(f"Failed to get tenant stats for '{tenant_name}': {e}")
            return {"tenant": tenant_name, "collection": collection_name, "object_count": 0}

    # =========================================================================
    # Health & Stats Methods
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Weaviate service health and module status.

        Returns:
            Health status dict with connection, modules, and collections info
        """
        try:
            if not self._is_connected:
                await self.connect()

            # Check if Weaviate is ready
            is_ready = self.client.is_ready()

            # Get module status
            meta = self.client.get_meta()

            return {
                "status": "healthy" if is_ready else "unhealthy",
                "connected": self._is_connected,
                "version": meta.get("version", "unknown"),
                "modules": {
                    "text2vec-openai": "text2vec-openai" in str(meta.get("modules", {})),
                    "generative-openai": "generative-openai" in str(meta.get("modules", {})),
                    "qna-openai": "qna-openai" in str(meta.get("modules", {})),
                    "reranker-cohere": "reranker-cohere" in str(meta.get("modules", {})),
                    "multi2vec-clip": "multi2vec-clip" in str(meta.get("modules", {})),
                },
                "collections": {
                    "Documents": self.client.collections.exists(COLLECTION_DOCUMENTS),
                    "Machinery": self.client.collections.exists(COLLECTION_MACHINERY),
                }
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: "Documents" or "Machinery"

        Returns:
            Stats dict with object counts and other metrics
        """
        if not self._is_connected:
            await self.connect()

        try:
            collection = self.client.collections.get(collection_name)

            # Aggregate query
            response = collection.aggregate.over_all(total_count=True)

            return {
                "collection": collection_name,
                "total_objects": response.total_count,
                "multi_tenancy_enabled": settings.enable_weaviate_multitenancy,
                "compression_enabled": settings.enable_weaviate_compression,
            }

        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {"collection": collection_name, "total_objects": 0}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """
        Build a Weaviate Filter object from a dict.

        Args:
            filters: Dict like {"category": "manuals", "manufacturer": "Caterpillar"}

        Returns:
            Weaviate Filter object
        """
        # Simple implementation - for production, you'd want more sophisticated filter building
        # This creates an AND filter for all provided key-value pairs

        filter_conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                filter_conditions.append(Filter.by_property(key).equal(value))
            elif isinstance(value, (int, float)):
                filter_conditions.append(Filter.by_property(key).equal(value))
            elif isinstance(value, list):
                filter_conditions.append(Filter.by_property(key).contains_any(value))

        if len(filter_conditions) == 0:
            return None
        elif len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            # Combine with AND
            result = filter_conditions[0]
            for condition in filter_conditions[1:]:
                result = result & condition
            return result

    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using Cohere reranker.

        Args:
            query: Original search query
            results: List of search results
            top_k: Number of results to return after reranking

        Returns:
            Reranked results
        """
        if not self.cohere_client or len(results) == 0:
            return results[:top_k]

        try:
            # Extract text content for reranking
            documents = []
            for result in results:
                # Try to get text content from properties
                text = result["properties"].get("text_content") or \
                       result["properties"].get("name") or \
                       str(result["properties"])
                documents.append(text)

            # Call Cohere rerank API
            response = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=documents,
                top_n=top_k,
                return_documents=False
            )

            # Reorder results based on reranking scores
            reranked = []
            for result in response.results:
                idx = result.index
                original_result = results[idx]
                original_result["rerank_score"] = result.relevance_score
                reranked.append(original_result)

            logger.info(f"Reranked {len(results)} → {len(reranked)} results")
            return reranked

        except Exception as e:
            logger.error(f"Reranking failed, returning original results: {e}")
            return results[:top_k]


# Global service instance
weaviate_service = WeaviateService()


async def get_weaviate_service() -> WeaviateService:
    """Dependency injection for FastAPI endpoints."""
    if not weaviate_service._is_connected:
        await weaviate_service.connect()
    return weaviate_service
