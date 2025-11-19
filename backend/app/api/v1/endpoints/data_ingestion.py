"""
API endpoints for machinery data ingestion

Handles JSON file uploads for bulk machinery data processing and
population into Pinecone vector database.

Endpoints:
- POST /upload: Upload and process machinery JSON file
- GET /status/{job_id}: Check ingestion job progress
- GET /list: List all ingestion jobs (admin only)
- DELETE /clear: Clear all machinery data (admin only)
"""

from fastapi import APIRouter, File, UploadFile, BackgroundTasks, HTTPException, Depends, Query
from typing import Dict, Any, Callable, Optional
import json
import logging
from datetime import datetime, UTC
import uuid

from app.services.data_ingestion_service import DataIngestionService, IngestionStats
from app.services.pinecone_service import get_pinecone_service
from app.api.v1.dependencies import require_admin, get_current_user
from app.models.user import UserModel
from app.schemas.data_ingestion import (
    IngestionJobResponse,
    IngestionStatusResponse,
    ClearDataResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for ingestion job status
# NOTE: In production, use Redis or database for persistence
ingestion_jobs: Dict[str, Dict[str, Any]] = {}


@router.options("/upload")
async def options_upload():
    """Handle CORS preflight for upload endpoint"""
    return {}


@router.post("/upload", response_model=IngestionJobResponse)
async def upload_machinery_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="JSON file with machinery data"),
    clear_existing: bool = Query(default=False, description="Clear existing data before ingestion"),
    current_user: UserModel = Depends(require_admin)
):
    """
    Upload and process machinery data JSON file (admin only)

    This endpoint accepts a JSON file containing machinery specifications and
    processes it in the background to populate:
    1. Pinecone vector database (for semantic search)

    The JSON structure should be:
    ```json
    {
        "Machine_SerialNumber": {
            "device_info": {
                "name": "Machine Name",
                "serial_number": "ABC123",
                "inventory_number": "INV456"
            },
            "properties": {
                "E1730 - Gewicht [kg]": {"value": "1200"},
                "E2760 - Truck - Assist": {"value": "Ja"}
            }
        }
    }
    ```

    Args:
        file: JSON file with machinery data (required)
        clear_existing: Whether to clear existing data in Pinecone first (default: False)
        current_user: Authenticated admin user

    Returns:
        Job ID and status for tracking progress

    Raises:
        HTTPException 400: Invalid JSON or file format
        HTTPException 403: User is not an admin
        HTTPException 500: Upload processing failed

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/data-ingestion/upload" \\
             -H "Authorization: Bearer YOUR_TOKEN" \\
             -F "file=@machinery.json" \\
             -F "clear_existing=true"
        ```
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail=f"File must be a JSON file. Received: {file.filename}"
        )

    try:
        # Read and validate JSON
        logger.info(f"Admin {current_user.username} uploading machinery data file: {file.filename}")
        contents = await file.read()

        try:
            machinery_data = json.loads(contents.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON format: {str(e)}"
            )

        # Validate structure
        if not isinstance(machinery_data, dict):
            raise HTTPException(
                status_code=400,
                detail="JSON must be a dictionary with machine IDs as keys"
            )

        if len(machinery_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="JSON file is empty - no machines found"
            )

        # Create job ID
        job_id = str(uuid.uuid4())

        # Initialize job status
        ingestion_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "total": len(machinery_data),
            "processed": 0,
            "failed": 0,
            "message": "Job queued for processing",
            "started_at": None,
            "completed_at": None,
            "errors": [],
            "result": None,
            "uploaded_by": current_user.username,
            "filename": file.filename
        }

        # Start background task
        background_tasks.add_task(
            process_machinery_data,
            job_id=job_id,
            machinery_data=machinery_data,
            clear_existing=clear_existing
        )

        logger.info(
            f"Ingestion job {job_id} queued by {current_user.username}: "
            f"{len(machinery_data)} machines, clear_existing={clear_existing}"
        )

        return IngestionJobResponse(
            job_id=job_id,
            status="queued",
            total_machines=len(machinery_data),
            message=f"Data ingestion started. Use GET /status/{job_id} to track progress."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    job_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get status of an ingestion job

    Returns real-time progress information for a running or completed
    ingestion job.

    Args:
        job_id: Job ID returned from /upload endpoint
        current_user: Authenticated user

    Returns:
        Detailed job status with progress information

    Raises:
        HTTPException 404: Job not found

    Example:
        ```bash
        curl "http://localhost:8000/api/data-ingestion/status/550e8400-e29b-41d4-a716-446655440000" \\
             -H "Authorization: Bearer YOUR_TOKEN"
        ```
    """
    if job_id not in ingestion_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found. It may have expired or never existed."
        )

    job_data = ingestion_jobs[job_id]

    return IngestionStatusResponse(
        job_id=job_data["job_id"],
        status=job_data["status"],
        progress=job_data["progress"],
        total=job_data["total"],
        processed=job_data["processed"],
        failed=job_data["failed"],
        message=job_data["message"],
        started_at=job_data.get("started_at"),
        completed_at=job_data.get("completed_at"),
        errors=job_data.get("errors", []),
        result=job_data.get("result")
    )


@router.get("/list")
async def list_ingestion_jobs(
    current_user: UserModel = Depends(require_admin)
):
    """
    List all ingestion jobs (admin only)

    Returns a summary of all ingestion jobs, including queued, processing,
    completed, and failed jobs.

    Args:
        current_user: Authenticated admin user

    Returns:
        Dictionary of all jobs with their statuses

    Raises:
        HTTPException 403: User is not an admin

    Example:
        ```bash
        curl "http://localhost:8000/api/data-ingestion/list" \\
             -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
        ```
    """
    return {
        "jobs": ingestion_jobs,
        "total": len(ingestion_jobs)
    }


@router.delete("/clear", response_model=ClearDataResponse)
async def clear_machinery_data(
    current_user: UserModel = Depends(require_admin)
):
    """
    Clear all machinery data from Pinecone (admin only)

    WARNING: This is a destructive operation that deletes ALL vectors
    in the 'machinery' namespace. This action cannot be undone.

    Use this endpoint to reset the machinery database before uploading
    new data or when you need to completely rebuild the index.

    Args:
        current_user: Authenticated admin user

    Returns:
        Success message

    Raises:
        HTTPException 403: User is not an admin
        HTTPException 500: Failed to clear data

    Example:
        ```bash
        curl -X DELETE "http://localhost:8000/api/data-ingestion/clear" \\
             -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
        ```
    """
    try:
        pinecone_service = get_pinecone_service()

        # Delete all vectors in machinery namespace
        await pinecone_service.delete_all_in_namespace("machinery")

        logger.warning(
            f"Admin {current_user.username} cleared all machinery data from Pinecone"
        )

        return ClearDataResponse(
            message="All machinery data cleared successfully",
            namespace="machinery"
        )

    except Exception as e:
        logger.error(f"Clear error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )




async def process_machinery_data(
    job_id: str,
    machinery_data: Dict[str, Any],
    clear_existing: bool
):
    """
    Background task to process machinery data

    This function runs asynchronously in the background to:
    1. Parse and validate machinery data
    2. Generate embeddings for semantic search
    3. Upload vectors to Pinecone
    4. Track progress and update job status

    Args:
        job_id: Job ID for tracking
        machinery_data: Parsed JSON data dictionary
        clear_existing: Whether to clear existing data first
    """
    try:
        # Update status
        ingestion_jobs[job_id]["status"] = "processing"
        ingestion_jobs[job_id]["started_at"] = datetime.now(UTC)
        ingestion_jobs[job_id]["message"] = "Initializing data ingestion..."

        logger.info(f"Starting ingestion job {job_id}")

        # Create service instance
        ingestion_service = DataIngestionService()

        # Process data with progress callback
        result = await ingestion_service.ingest_from_dict(
            machinery_data=machinery_data,
            clear_existing=clear_existing,
            progress_callback=lambda current, total, msg: update_job_progress(
                job_id, current, total, msg
            )
        )

        # Update final status
        ingestion_jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "processed": result["successful"],
            "failed": result["failed"],
            "completed_at": datetime.now(UTC),
            "message": "Ingestion completed successfully",
            "result": result
        })

        logger.info(
            f"Ingestion job {job_id} completed: "
            f"{result['successful']}/{result['total']} successful, "
            f"{result['failed']} failed"
        )

    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {str(e)}", exc_info=True)
        ingestion_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now(UTC),
            "message": f"Ingestion failed: {str(e)}",
            "errors": [str(e)]
        })


def update_job_progress(job_id: str, current: int, total: int, message: str):
    """
    Update job progress during processing

    Args:
        job_id: Job ID to update
        current: Current number of items processed
        total: Total number of items to process
        message: Status message
    """
    if job_id in ingestion_jobs:
        progress = int((current / total) * 100) if total > 0 else 0
        ingestion_jobs[job_id].update({
            "processed": current,
            "progress": progress,
            "message": message
        })

        # Log progress at milestones
        if progress % 25 == 0 and progress > 0:
            logger.info(f"Job {job_id}: {progress}% complete - {message}")
