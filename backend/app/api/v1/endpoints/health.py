"""
Health check endpoints for monitoring and deployment verification.
"""
import logging
from datetime import datetime, UTC
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Header

from app.config import settings
from app.core.database import health_check as db_health_check

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

    # TODO: Add Pinecone health check
    services_status["pinecone"] = {
        "status": "not_implemented",
        "healthy": True,  # Default to true for now
    }

    # TODO: Add PostgreSQL API health check
    services_status["postgresql_api"] = {
        "status": "not_implemented",
        "healthy": True,  # Default to true for now
    }

    # TODO: Add OpenAI API health check
    services_status["openai"] = {
        "status": "not_implemented",
        "healthy": True,  # Default to true for now
    }

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
