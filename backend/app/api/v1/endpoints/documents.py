"""
Document Management Endpoints

Handles document upload, listing, and deletion:
- POST /upload - Upload and process documents (superuser/admin only)
- GET / - List documents with filters and pagination
- DELETE /{document_id} - Delete document from Pinecone and MongoDB
"""

import logging
import os
import uuid
import shutil
import json
import asyncio
import time
from datetime import datetime, UTC
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.api.v1.dependencies import require_superuser, get_current_user
from app.core.database import get_database
from app.models.user import UserModel
from app.models.document import DocumentMetadataModel
from app.models.audit_log import AuditLogModel
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentDeleteResponse
)
from app.services.document_processor import get_document_processor
from app.services.pinecone_service import get_pinecone_service
from app.services.document_events import get_document_events_manager
from app.services.upload_queue_service import get_queue_service
from app.config import get_settings
from app.utils.query_monitor import QueryPerformanceMonitor, with_timeout

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.ppt', '.jpg', '.jpeg', '.png', '.gif'}

# Temporary upload directory
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and process document",
    description="Upload a document for OCR processing and vector storage (superuser/admin only)"
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    category: str = Form(..., description="Document category"),
    user: UserModel = Depends(require_superuser)
):
    """
    Upload document and queue for background processing

    - **file**: Document file (PDF, DOCX, PPTX, XLSX, XLS, PPT, JPG, JPEG, PNG, GIF)
    - **category**: Document category for organization
    - **Returns**: document_id and status (uploading)

    Background processing:
    1. Extract text with Docling OCR
    2. Chunk text (~500 tokens with 50 token overlap)
    3. Generate embeddings (OpenAI text-embedding-3-large)
    4. Store vectors in Pinecone
    5. Update status to 'completed'
    """
    try:
        # Validate file extension
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Save file temporarily
        file_ext = os.path.splitext(file.filename)[1].lower()
        temp_filename = f"{document_id}{file_ext}"
        temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)

        # Write uploaded file to disk
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(temp_filepath)

        logger.info(
            f"Document uploaded: {file.filename} ({file_size} bytes) "
            f"by user {user.username}"
        )

        # Don't create document metadata yet - it will be created when queue processor
        # picks it up for processing. This avoids showing documents twice.
        db = get_database()

        # Add to processing queue
        queue_service = get_queue_service(db)
        queue_item = await queue_service.add_to_queue(
            document_id=document_id,
            filename=file.filename,
            category=category,
            file_path=temp_filepath,
            file_size_bytes=file_size,
            uploader_id=user.user_id,
            uploader_name=user.username,
        )

        logger.info(
            f"Added document {document_id} to queue at position {queue_item.position}"
        )

        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "queued",
            "queue_position": queue_item.position,
            "message": f"Document uploaded and queued at position {queue_item.position}. Processing will start automatically."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )
    finally:
        # Close file handle
        await file.close()


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Get list of documents with optional filters (superuser/admin only)"
)
async def list_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    user: UserModel = Depends(require_superuser)
):
    """
    List documents with filtering and pagination

    Query Parameters:
    - **category**: Filter by document category
    - **search**: Search in filename (case-insensitive regex)
    - **uploaded_by**: Filter by uploader username
    - **start_date**: Filter documents uploaded after this date
    - **end_date**: Filter documents uploaded before this date
    - **limit**: Maximum number of documents to return (default 50, max 100)
    - **offset**: Number of documents to skip (default 0)

    Returns:
    - List of documents with metadata
    - Total count for pagination
    """
    start_time = time.time()

    try:
        db = get_database()

        # Enforce maximum limit to prevent performance issues
        limit = min(limit, 100)

        # Build query filter
        query_filter = {"deleted": False}

        if category:
            query_filter["category"] = category

        if search:
            # Case-insensitive regex search on filename
            query_filter["filename"] = {"$regex": search, "$options": "i"}

        if uploaded_by:
            query_filter["uploader_name"] = uploaded_by

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query_filter["upload_date"] = date_filter

        # Get total count with timeout protection
        # Use estimated count for better performance when no filters
        with QueryPerformanceMonitor("document_count", warn_threshold=2.0):
            if len(query_filter) == 1:  # Only 'deleted' filter
                # Use fast estimated count for unfiltered queries
                total = await with_timeout(
                    db.document_metadata.estimated_document_count(),
                    timeout=5.0,
                    operation_name="estimated_document_count",
                    fallback_value=0,
                    raise_on_timeout=False
                )
            else:
                # Use accurate count for filtered queries
                total = await with_timeout(
                    db.document_metadata.count_documents(query_filter),
                    timeout=8.0,
                    operation_name="count_documents with filters",
                    fallback_value=0,
                    raise_on_timeout=False
                )

        # Get documents with pagination and timeout protection
        with QueryPerformanceMonitor("document_fetch", warn_threshold=3.0):
            cursor = db.document_metadata.find(query_filter)\
                .sort("upload_date", -1)\
                .skip(offset)\
                .limit(limit)

            # Wrap cursor iteration in timeout
            async def fetch_documents():
                docs = []
                async for doc in cursor:
                    docs.append(DocumentResponse(
                        document_id=doc["document_id"],
                        filename=doc["filename"],
                        category=doc["category"],
                        upload_date=doc["upload_date"],
                        uploader_name=doc["uploader_name"],
                        uploader_id=doc["uploader_id"],
                        file_size_bytes=doc["file_size_bytes"],
                        processing_status=doc["processing_status"],
                        processing_step=doc.get("processing_step"),
                        processing_progress=doc.get("processing_progress"),
                        chunk_count=doc.get("chunk_count"),
                        error_message=doc.get("error_message")
                    ))
                return docs

            try:
                documents = await with_timeout(
                    fetch_documents(),
                    timeout=15.0,
                    operation_name="fetch_documents cursor iteration",
                    raise_on_timeout=True
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Document query timed out. Try narrowing your search filters or reducing the page size."
                )

        total_time = time.time() - start_time
        logger.info(
            f"Listed {len(documents)} documents (total: {total}) "
            f"for user {user.username} in {total_time:.2f}s"
        )

        return DocumentListResponse(
            documents=documents,
            total=total,
            limit=limit,
            offset=offset
        )

    except asyncio.TimeoutError:
        # Already handled above, but catch any other timeout
        logger.error("Document listing timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. Please try again with more specific filters."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document listing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document",
    description="Delete document from Pinecone and soft delete in MongoDB (superuser/admin only)"
)
async def delete_document(
    document_id: str,
    hard_delete: bool = False,
    user: UserModel = Depends(require_superuser)
):
    """
    Delete document

    - **document_id**: ID of document to delete
    - **hard_delete**: If true, permanently delete from MongoDB (default: false for soft delete)

    Process:
    1. Verify document exists
    2. Delete all vectors from Pinecone
    3. Soft delete in MongoDB (or hard delete if requested)
    4. Create audit log entry

    Returns:
    - Success status and message
    """
    try:
        db = get_database()

        # Look up document
        document = await db.document_metadata.find_one({"document_id": document_id})

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        # Check if already deleted
        if document.get("deleted", False) and not hard_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document already deleted"
            )

        # Delete from Pinecone
        pinecone_service = get_pinecone_service()

        try:
            await pinecone_service.delete_vectors_by_filter(
                filter={"document_id": document_id}
            )
            logger.info(f"Deleted vectors for document {document_id} from Pinecone")
        except Exception as e:
            logger.error(f"Pinecone deletion failed for {document_id}: {str(e)}")
            # Continue with MongoDB deletion even if Pinecone fails

        # Delete from MongoDB
        if hard_delete:
            # Permanent deletion
            result = await db.document_metadata.delete_one({"document_id": document_id})

            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete document from database"
                )

            logger.info(f"Hard deleted document {document_id} from MongoDB")
            deletion_type = "permanent"

        else:
            # Soft delete
            result = await db.document_metadata.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "deleted": True,
                        "deleted_at": datetime.now(UTC),
                        "deleted_by": user.user_id
                    }
                }
            )

            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update document deletion status"
                )

            logger.info(f"Soft deleted document {document_id} from MongoDB")
            deletion_type = "soft"

        # Create audit log entry
        audit_log = AuditLogModel(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            admin_user_id=user.user_id,
            admin_username=user.username,
            action_type="delete_document",
            target_user_id=None,
            target_username=None,
            details={
                "document_id": document_id,
                "filename": document.get("filename"),
                "deletion_type": deletion_type,
                "category": document.get("category")
            }
        )

        await db.audit_logs.insert_one(audit_log.model_dump())

        logger.info(
            f"Document {document_id} deleted by {user.username} "
            f"(type: {deletion_type})"
        )

        return DocumentDeleteResponse(
            success=True,
            message=f"Document {'permanently' if hard_delete else 'successfully'} deleted",
            document_id=document_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion failed: {str(e)}"
        )


@router.get(
    "/stream/{document_id}",
    summary="Stream document processing updates",
    description="Server-Sent Events endpoint for real-time document processing status updates"
)
async def stream_document_updates(
    document_id: str,
    user: UserModel = Depends(require_superuser)
):
    """
    Stream real-time document processing updates via Server-Sent Events (SSE)

    - **document_id**: Document ID to monitor
    - Returns: SSE stream with processing status updates

    The stream will automatically close when:
    - Document processing completes (status: completed)
    - Document processing fails (status: failed)
    - Client disconnects

    Event format:
    ```
    data: {"document_id": "...", "processing_status": "processing", ...}
    ```
    """

    async def event_generator():
        """Generate SSE events for document processing updates"""
        events_manager = get_document_events_manager()
        queue = await events_manager.subscribe(document_id)

        try:
            logger.info(f"Client connected to document {document_id} SSE stream")

            # Send initial connection confirmation
            yield json.dumps({'type': 'connected', 'document_id': document_id})

            # Listen for updates with timeout
            while True:
                try:
                    # Wait for update with 30-second timeout
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Send update to client
                    yield json.dumps(update)

                    # Check if processing is complete (terminal state)
                    if update.get('processing_status') in ['completed', 'failed']:
                        logger.info(
                            f"Document {document_id} processing finished with status: "
                            f"{update.get('processing_status')}"
                        )
                        # Send final done signal
                        yield json.dumps({'type': 'done'})
                        break

                except asyncio.TimeoutError:
                    # Send keepalive ping (comment in SSE)
                    from sse_starlette.sse import ServerSentEvent
                    yield ServerSentEvent(comment="keepalive")

        except asyncio.CancelledError:
            logger.info(f"Client disconnected from document {document_id} SSE stream")
            raise
        except Exception as e:
            logger.error(f"Error in SSE stream for document {document_id}: {str(e)}")
            yield json.dumps({'type': 'error', 'message': str(e)})
        finally:
            # Clean up subscription
            await events_manager.unsubscribe(document_id, queue)

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
