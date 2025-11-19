"""
Pydantic schemas for data ingestion API

Models for machinery data upload, processing status, and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class IngestionJobResponse(BaseModel):
    """Response when starting an ingestion job"""
    job_id: str = Field(description="Unique job identifier for tracking")
    status: str = Field(description="Job status: queued, processing, completed, failed")
    total_machines: int = Field(description="Total number of machines to process")
    message: str = Field(description="Human-readable status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "total_machines": 842,
                "message": "Data ingestion started. Use /status/{job_id} to track progress."
            }
        }
    }


class Neo4jIngestionResult(BaseModel):
    """Neo4j ingestion results"""
    machines_processed: int = Field(default=0, description="Number of machines processed")
    machines_created: int = Field(default=0, description="Number of machines created")
    machines_skipped: int = Field(default=0, description="Number of machines skipped")
    machines_failed: int = Field(default=0, description="Number of machines failed")
    properties_created: int = Field(default=0, description="Number of property definitions created")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    error_count: int = Field(default=0, description="Number of errors")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Error details")
    error: Optional[str] = Field(default=None, description="Fatal error message if migration failed")


class IngestionStatusResponse(BaseModel):
    """Detailed status of an ingestion job"""
    job_id: str = Field(description="Job identifier")
    status: str = Field(description="Current status: queued, processing, completed, failed")
    progress: int = Field(description="Progress percentage (0-100)")
    total: int = Field(description="Total machines to process")
    processed: int = Field(description="Number of machines processed so far")
    failed: int = Field(description="Number of machines that failed")
    message: str = Field(description="Current status message")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final ingestion results")
    neo4j: Optional[Dict[str, Any]] = Field(default=None, description="Neo4j ingestion results")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 45,
                "total": 842,
                "processed": 379,
                "failed": 0,
                "message": "Creating embeddings... batch 19/43",
                "started_at": "2025-11-13T10:30:00Z",
                "completed_at": None,
                "errors": []
            }
        }
    }


class IngestionJobList(BaseModel):
    """List of all ingestion jobs"""
    jobs: Dict[str, IngestionStatusResponse] = Field(description="All jobs by job_id")
    total: int = Field(description="Total number of jobs")

    model_config = {
        "json_schema_extra": {
            "example": {
                "jobs": {},
                "total": 0
            }
        }
    }


class ClearDataResponse(BaseModel):
    """Response when clearing machinery data"""
    message: str = Field(description="Success message")
    namespace: str = Field(default="machinery", description="Namespace that was cleared")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "All machinery data cleared successfully",
                "namespace": "machinery"
            }
        }
    }
