"""Document schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """Document upload request schema."""
    category: str = Field(max_length=100, description="Document category")


class DocumentResponse(BaseModel):
    """Document response schema."""
    document_id: str = Field(description="Document ID")
    filename: str = Field(description="Original filename")
    category: str = Field(description="Document category")
    upload_date: datetime = Field(description="Upload timestamp")
    uploader_name: str = Field(description="Username of uploader")
    uploader_id: str = Field(description="User ID of uploader")
    file_size_bytes: int = Field(description="File size in bytes")
    processing_status: str = Field(description="Processing status: uploading, processing, completed, failed")
    processing_step: Optional[str] = Field(default=None, description="Current processing step")
    processing_progress: Optional[int] = Field(default=None, description="Processing progress percentage (0-100)")
    chunk_count: Optional[int] = Field(default=None, description="Number of chunks created")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")


class DocumentListResponse(BaseModel):
    """Document list response schema."""
    documents: List[DocumentResponse] = Field(description="List of documents")
    total: int = Field(description="Total number of documents")
    limit: int = Field(description="Limit used in query")
    offset: int = Field(description="Offset used in query")


class DocumentDeleteResponse(BaseModel):
    """Document deletion response schema."""
    success: bool = Field(description="Whether deletion was successful")
    message: str = Field(description="Status message")
    document_id: str = Field(description="Deleted document ID")
