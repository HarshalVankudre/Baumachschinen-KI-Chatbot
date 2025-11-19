"""Document metadata model for MongoDB."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentMetadataModel(BaseModel):
    """Document metadata document model for MongoDB."""
    document_id: str = Field(description="Unique document ID")
    filename: str = Field(description="Original filename")
    category: str = Field(description="Document category")
    uploader_id: str = Field(description="User ID of uploader")
    uploader_name: str = Field(description="Username of uploader")
    upload_date: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Upload timestamp")
    file_size_bytes: int = Field(description="File size in bytes")
    file_extension: str = Field(description="File extension")
    processing_status: str = Field(default="uploading", description="Processing status")
    processing_step: Optional[str] = Field(default=None, description="Current processing step")
    processing_progress: Optional[int] = Field(default=None, description="Processing progress percentage (0-100)")
    chunk_count: Optional[int] = Field(default=None, description="Number of chunks created")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")
    deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_by: Optional[str] = Field(default=None, description="User ID who deleted")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "doc-550e8400",
                "filename": "CAT_320_Manual.pdf",
                "category": "equipment_manuals",
                "uploader_id": "user-123",
                "uploader_name": "admin",
                "file_size_bytes": 5242880,
                "file_extension": ".pdf",
                "processing_status": "completed",
                "chunk_count": 45,
            }
        }
    )
