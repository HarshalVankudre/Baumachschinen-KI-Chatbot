"""
MongoDB Schema Validation for Document Metadata Collection (DB-009)
Tracks uploaded documents and their processing status
"""

from datetime import datetime
from typing import Optional, List

# Document Metadata Collection Schema Validation
DOCUMENT_METADATA_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "document_id",
            "filename",
            "category",
            "upload_date",
            "uploader_user_id",
            "processing_status",
            "deleted"
        ],
        "properties": {
            "_id": {
                "bsonType": "objectId"
            },
            "document_id": {
                "bsonType": "string",
                "description": "UUID string (unique identifier)",
                "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
            },
            "pinecone_ids": {
                "bsonType": "array",
                "description": "Array of Pinecone vector IDs",
                "items": {"bsonType": "string"}
            },
            "filename": {
                "bsonType": "string",
                "description": "Original filename",
                "maxLength": 255
            },
            "file_type": {
                "bsonType": ["string", "null"],
                "description": "File extension (pdf, docx, etc)"
            },
            "file_size_bytes": {
                "bsonType": ["int", "long", "null"],
                "description": "File size in bytes",
                "minimum": 0
            },
            "category": {
                "bsonType": "string",
                "description": "Document category"
            },
            "upload_date": {
                "bsonType": "date",
                "description": "Upload timestamp"
            },
            "uploader_user_id": {
                "bsonType": "string",
                "description": "User who uploaded document"
            },
            "uploader_name": {
                "bsonType": ["string", "null"],
                "description": "Uploader name (denormalized)"
            },
            "processing_status": {
                "enum": ["uploading", "processing", "completed", "failed"],
                "description": "Processing status"
            },
            "processing_started_at": {
                "bsonType": ["date", "null"],
                "description": "Processing start timestamp"
            },
            "processing_completed_at": {
                "bsonType": ["date", "null"],
                "description": "Processing completion timestamp"
            },
            "processing_error": {
                "bsonType": ["string", "null"],
                "description": "Error message if processing failed"
            },
            "chunk_count": {
                "bsonType": "int",
                "description": "Number of chunks/vectors created",
                "minimum": 0
            },
            "embedding_model": {
                "bsonType": ["string", "null"],
                "description": "Embedding model used"
            },
            "deleted": {
                "bsonType": "bool",
                "description": "Soft delete flag"
            },
            "deleted_at": {
                "bsonType": ["date", "null"],
                "description": "Deletion timestamp"
            },
            "deleted_by": {
                "bsonType": ["string", "null"],
                "description": "User who deleted document"
            }
        }
    }
}


def get_document_metadata_collection_options():
    """
    Get collection options for document metadata collection

    Returns:
        Dictionary of collection options
    """
    return {
        "validator": DOCUMENT_METADATA_SCHEMA,
        "validationLevel": "strict",
        "validationAction": "error"
    }


def create_document_metadata_document(
    document_id: str,
    filename: str,
    category: str,
    uploader_user_id: str,
    uploader_name: Optional[str] = None,
    file_type: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
    embedding_model: str = "text-embedding-3-large"
) -> dict:
    """
    Create a document metadata document

    Args:
        document_id: UUID string
        filename: Original filename
        category: Document category
        uploader_user_id: User who uploaded
        uploader_name: Uploader's name
        file_type: File extension
        file_size_bytes: File size
        embedding_model: Embedding model name

    Returns:
        Document metadata dictionary
    """
    return {
        "document_id": document_id,
        "pinecone_ids": [],
        "filename": filename,
        "file_type": file_type,
        "file_size_bytes": file_size_bytes,
        "category": category,
        "upload_date": datetime.utcnow(),
        "uploader_user_id": uploader_user_id,
        "uploader_name": uploader_name,
        "processing_status": "uploading",
        "processing_started_at": None,
        "processing_completed_at": None,
        "processing_error": None,
        "chunk_count": 0,
        "embedding_model": embedding_model,
        "deleted": False,
        "deleted_at": None,
        "deleted_by": None
    }
