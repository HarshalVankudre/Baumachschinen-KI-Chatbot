"""
Main FastAPI application for Building Machinery AI Chatbot.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.logging_config import setup_logging
from app.api.v1 import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# Initialize Sentry if DSN provided
if settings.sentry_dsn and settings.sentry_dsn.startswith(("https://", "http://")):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1 if settings.is_production else 1.0,
    )
    logger.info("Sentry initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting Building Machinery AI Chatbot API - Environment: {settings.environment}")

    # Connect to MongoDB
    await connect_to_mongo()
    logger.info("MongoDB connected")

    # Recover orphaned document processing jobs (from server restart/crash)
    await recover_orphaned_processes()

    # Start the queue processor
    from app.services.upload_queue_service import start_queue_processor
    from app.core.database import get_database
    processor_task = await start_queue_processor(get_database())
    logger.info("Queue processor started")

    # TODO: Initialize other services (Pinecone, OpenAI clients) if needed

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Cancel queue processor
    if processor_task and not processor_task.done():
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            pass
        logger.info("Queue processor stopped")

    await close_mongo_connection()
    logger.info("MongoDB connection closed")


async def recover_orphaned_processes():
    """
    Mark abandoned processing jobs as failed on server startup.

    If the server restarts/crashes while documents are processing,
    those background tasks are lost. This function detects such
    "orphaned" documents and marks them as failed so users know
    they need to re-upload.
    """
    from datetime import datetime, timedelta, UTC
    from app.core.database import get_database

    try:
        db = get_database()

        # Find documents that have been in "processing" or "uploading" state
        # for more than 30 minutes (reasonable max time for any document)
        cutoff_time = datetime.now(UTC) - timedelta(minutes=30)

        result = await db.document_metadata.update_many(
            {
                "processing_status": {"$in": ["processing", "uploading"]},
                "upload_date": {"$lt": cutoff_time}
            },
            {
                "$set": {
                    "processing_status": "failed",
                    "error_message": "Processing interrupted by server restart. Please re-upload the document."
                }
            }
        )

        if result.modified_count > 0:
            logger.warning(
                f"Recovered {result.modified_count} orphaned document processing jobs. "
                "These documents were marked as failed due to server restart."
            )
        else:
            logger.info("No orphaned document processing jobs found")

    except Exception as e:
        logger.error(f"Failed to recover orphaned processes: {str(e)}")
        # Don't fail startup if recovery fails
        pass


# Create FastAPI application
app = FastAPI(
    title="Building Machinery AI Chatbot API",
    description="Enterprise AI Chatbot System for Building Machinery Support",
    version="1.0.0",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Setup Prometheus metrics
if settings.environment != "development":
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics enabled at /metrics")


# Include API router
app.include_router(api_router, prefix="/api")


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": "Building Machinery AI Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
