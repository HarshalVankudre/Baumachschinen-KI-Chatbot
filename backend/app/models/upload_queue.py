"""
Upload Queue Model

Stores documents waiting to be processed in a server-side queue.
Ensures sequential processing across all users.
"""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field


class UploadQueueModel(BaseModel):
    """Document in the upload queue"""

    queue_id: str = Field(..., description="Unique queue item ID")
    document_id: str = Field(..., description="Document ID from document_metadata")
    filename: str = Field(..., description="Original filename")
    category: str = Field(..., description="Document category")
    file_path: str = Field(..., description="Path to uploaded file on server")
    file_size_bytes: int = Field(..., description="File size in bytes")

    # User info
    uploader_id: str = Field(..., description="User ID who uploaded")
    uploader_name: str = Field(..., description="Username who uploaded")

    # Queue status
    status: str = Field(
        default="pending",
        description="Queue status: pending, processing, completed, failed"
    )
    position: int = Field(..., description="Position in queue (1-indexed)")

    # Timestamps
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Processing info
    processing_progress: Optional[int] = Field(default=0, ge=0, le=100)
    processing_step: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "queue_id": "queue_abc123",
                "document_id": "doc_xyz789",
                "filename": "manual.pdf",
                "category": "manuals",
                "file_path": "/tmp/uploads/doc_xyz789.pdf",
                "file_size_bytes": 1048576,
                "uploader_id": "user123",
                "uploader_name": "john.doe",
                "status": "pending",
                "position": 3,
                "added_at": "2024-01-15T10:30:00Z",
                "processing_progress": 0,
            }
        }
