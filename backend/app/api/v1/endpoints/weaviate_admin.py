"""
Weaviate Admin Endpoints

Advanced administration endpoints for Weaviate:
- GraphQL query execution
- Tenant management (list, create, delete)
- Collection statistics
- Hybrid search testing with alpha tuning
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.api.v1.dependencies import require_superuser
from app.models.user import UserModel
from app.services.weaviate_service import weaviate_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weaviate", tags=["Weaviate Admin"])
settings = get_settings()


# Request/Response Schemas
class GraphQLQueryRequest(BaseModel):
    """GraphQL query request schema"""
    query: str = Field(..., description="GraphQL query string")
    collection: Optional[str] = Field(default=None, description="Optional collection filter")


class GraphQLQueryResponse(BaseModel):
    """GraphQL query response schema"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TenantCreateRequest(BaseModel):
    """Tenant creation request schema"""
    tenant_name: str = Field(..., min_length=1, max_length=100, description="Tenant identifier")
    collection: str = Field(..., description="Collection name (Documents or Machinery)")


class TenantListResponse(BaseModel):
    """Tenant list response schema"""
    collection: str
    tenants: List[Dict[str, Any]]
    total: int


class HybridSearchTestRequest(BaseModel):
    """Hybrid search test request schema"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    collection: str = Field(..., description="Collection to search (Documents or Machinery)")
    alpha: float = Field(default=0.75, ge=0.0, le=1.0, description="Hybrid search alpha (0.0=BM25, 1.0=vector)")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    enable_rerank: bool = Field(default=True, description="Enable Cohere reranking")
    tenant: Optional[str] = Field(default=None, description="Optional tenant filter")


class HybridSearchTestResponse(BaseModel):
    """Hybrid search test response schema"""
    query: str
    collection: str
    alpha: float
    reranking_enabled: bool
    results: List[Dict[str, Any]]
    total_results: int
    search_time_ms: float


@router.post(
    "/graphql",
    response_model=GraphQLQueryResponse,
    summary="Execute GraphQL query",
    description="Execute raw GraphQL query against Weaviate (superuser only)"
)
async def execute_graphql(
    request: GraphQLQueryRequest,
    user: UserModel = Depends(require_superuser)
) -> GraphQLQueryResponse:
    """
    Execute GraphQL query against Weaviate

    Allows running custom GraphQL queries for:
    - Complex data retrieval
    - Schema inspection
    - Advanced filtering
    - Aggregations

    Example query:
    ```graphql
    {
      Get {
        Documents {
          filename
          category
          text_content
        }
      }
    }
    ```
    """
    try:
        logger.info(f"Executing GraphQL query by {user.username}: {request.query[:100]}...")

        result = await weaviate_service.query_graphql(request.query)

        return GraphQLQueryResponse(
            success=True,
            data=result
        )

    except Exception as e:
        logger.error(f"GraphQL query failed: {str(e)}", exc_info=True)
        return GraphQLQueryResponse(
            success=False,
            error=str(e)
        )


@router.get(
    "/tenants/{collection}",
    response_model=TenantListResponse,
    summary="List tenants",
    description="List all tenants for a collection (superuser only)"
)
async def list_tenants(
    collection: str,
    user: UserModel = Depends(require_superuser)
) -> TenantListResponse:
    """
    List all tenants for a collection

    Collections:
    - Documents: Document tenants (one per uploader)
    - Machinery: Machinery data tenants
    """
    try:
        logger.info(f"Listing tenants for collection {collection} by {user.username}")

        tenants = await weaviate_service.list_tenants(collection)

        return TenantListResponse(
            collection=collection,
            tenants=tenants,
            total=len(tenants)
        )

    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.post(
    "/tenants",
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
    description="Create new tenant for a collection (superuser only)"
)
async def create_tenant(
    request: TenantCreateRequest,
    user: UserModel = Depends(require_superuser)
):
    """
    Create new tenant for a collection

    Tenants provide data isolation at the collection level.
    Each tenant has dedicated shards for performance.
    """
    try:
        logger.info(
            f"Creating tenant '{request.tenant_name}' in {request.collection} "
            f"by {user.username}"
        )

        await weaviate_service.create_tenant(request.collection, request.tenant_name)

        return {
            "success": True,
            "message": f"Tenant '{request.tenant_name}' created in {request.collection}",
            "tenant": request.tenant_name,
            "collection": request.collection
        }

    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.delete(
    "/tenants/{collection}/{tenant_name}",
    summary="Delete tenant",
    description="Delete tenant and all its data (superuser only)"
)
async def delete_tenant(
    collection: str,
    tenant_name: str,
    user: UserModel = Depends(require_superuser)
):
    """
    Delete tenant and all its data

    WARNING: This permanently deletes all data for the tenant.
    This action cannot be undone.
    """
    try:
        logger.warning(
            f"Deleting tenant '{tenant_name}' from {collection} by {user.username}"
        )

        await weaviate_service.delete_tenant(collection, tenant_name)

        return {
            "success": True,
            "message": f"Tenant '{tenant_name}' deleted from {collection}",
            "tenant": tenant_name,
            "collection": collection
        }

    except Exception as e:
        logger.error(f"Failed to delete tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tenant: {str(e)}"
        )


@router.get(
    "/stats/{collection}",
    summary="Get collection statistics",
    description="Get statistics for a Weaviate collection (superuser only)"
)
async def get_collection_stats(
    collection: str,
    user: UserModel = Depends(require_superuser)
):
    """
    Get collection statistics

    Returns:
    - Total objects
    - Multi-tenancy status
    - Compression status
    - Vectorizer configuration
    """
    try:
        logger.info(f"Getting stats for collection {collection} by {user.username}")

        stats = await weaviate_service.get_collection_stats(collection)

        return {
            "success": True,
            "collection": collection,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get collection stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection stats: {str(e)}"
        )


@router.post(
    "/search/test",
    response_model=HybridSearchTestResponse,
    summary="Test hybrid search",
    description="Test hybrid search with different alpha values (superuser only)"
)
async def test_hybrid_search(
    request: HybridSearchTestRequest,
    user: UserModel = Depends(require_superuser)
) -> HybridSearchTestResponse:
    """
    Test hybrid search with configurable parameters

    Use this endpoint to experiment with:
    - Different alpha values (keyword vs vector balance)
    - Reranking on/off comparison
    - Tenant-specific searches

    Alpha values:
    - 0.0 = Pure BM25 keyword search
    - 0.5 = Balanced hybrid
    - 0.75 = Default (75% vector, 25% keyword)
    - 1.0 = Pure vector search
    """
    import time

    try:
        logger.info(
            f"Testing hybrid search by {user.username}: "
            f"query='{request.query[:50]}...', alpha={request.alpha}, "
            f"rerank={request.enable_rerank}"
        )

        start_time = time.time()

        results = await weaviate_service.query_hybrid(
            query=request.query,
            collection_name=request.collection,
            alpha=request.alpha,
            top_k=request.top_k,
            tenant=request.tenant,
            enable_rerank=request.enable_rerank
        )

        elapsed_ms = (time.time() - start_time) * 1000

        # Format results for response
        formatted_results = []
        for result in results:
            properties = result.get("properties", {})
            formatted_results.append({
                "uuid": result.get("uuid"),
                "score": result.get("score", 0.0),
                "properties": properties
            })

        return HybridSearchTestResponse(
            query=request.query,
            collection=request.collection,
            alpha=request.alpha,
            reranking_enabled=request.enable_rerank,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time_ms=round(elapsed_ms, 2)
        )

    except Exception as e:
        logger.error(f"Hybrid search test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search test failed: {str(e)}"
        )


@router.get(
    "/modules",
    summary="Get Weaviate modules status",
    description="Get status of all Weaviate modules (superuser only)"
)
async def get_modules_status(
    user: UserModel = Depends(require_superuser)
):
    """
    Get Weaviate modules status

    Returns status of:
    - text2vec-openai (embeddings)
    - generative-openai (RAG)
    - qna-openai (Q&A)
    - reranker-cohere (reranking)
    """
    try:
        logger.info(f"Getting Weaviate modules status by {user.username}")

        health = await weaviate_service.health_check()

        return {
            "success": True,
            "version": health.get("version"),
            "modules": health.get("modules", {}),
            "collections": health.get("collections", {})
        }

    except Exception as e:
        logger.error(f"Failed to get modules status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modules status: {str(e)}"
        )
