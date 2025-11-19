"""
Health check endpoints for monitoring and deployment verification.
"""
import logging
from datetime import datetime, UTC
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Header

from app.config import settings
from app.core.database import health_check as db_health_check
from app.services.hybrid_retrieval_orchestrator import get_hybrid_retrieval_orchestrator
from app.services.retrieval_telemetry import get_retrieval_telemetry
from app.services.weaviate_service import weaviate_service
from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def basic_health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    No authentication required. Used by load balancers and monitoring.

    Returns:
        dict: Health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "Building Machinery AI Chatbot API",
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(
    x_api_key: str = Header(..., description="Internal API key")
) -> Dict[str, Any]:
    """
    Detailed health check endpoint with dependency checks.
    Requires internal API key for security.

    Args:
        x_api_key: Internal API key from header

    Returns:
        dict: Detailed health status for all services

    Raises:
        HTTPException: 401 if API key is invalid, 503 if services are unhealthy
    """
    # Verify internal API key
    if x_api_key != settings.api_internal_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    services_status = {}
    overall_healthy = True

    # Check MongoDB
    try:
        db_healthy = await db_health_check()
        services_status["mongodb"] = {
            "status": "connected" if db_healthy else "disconnected",
            "healthy": db_healthy,
        }
        if not db_healthy:
            overall_healthy = False
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        services_status["mongodb"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }
        overall_healthy = False

    # Check Weaviate
    try:
        weaviate_health = await weaviate_service.health_check()

        weaviate_healthy = weaviate_health.get("status") == "healthy"
        services_status["weaviate"] = {
            "status": weaviate_health.get("status", "unknown"),
            "healthy": weaviate_healthy,
            "version": weaviate_health.get("version", "unknown"),
            "modules": weaviate_health.get("modules", {}),
            "collections": weaviate_health.get("collections", {}),
        }

        if not weaviate_healthy:
            overall_healthy = False

    except Exception as e:
        logger.error(f"Weaviate health check failed: {e}")
        services_status["weaviate"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }
        overall_healthy = False

    # Check OpenAI API
    try:
        openai_service = get_openai_service()
        # Quick embedding test to verify API connectivity
        test_embedding = await openai_service.create_embedding("health check")

        openai_healthy = len(test_embedding) > 0
        services_status["openai"] = {
            "status": "connected" if openai_healthy else "disconnected",
            "healthy": openai_healthy,
            "model": settings.openai_chat_model,
            "embedding_model": settings.openai_embedding_model,
            "embedding_dimensions": len(test_embedding) if openai_healthy else 0,
        }

        if not openai_healthy:
            overall_healthy = False

    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        services_status["openai"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }
        overall_healthy = False

    response = {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "services": services_status,
        "environment": settings.environment,
    }

    # Return 503 if any critical service is down
    if not overall_healthy:
        raise HTTPException(status_code=503, detail=response)

    return response


# Advanced RAG and Phase 4 health check endpoints removed in simplification
