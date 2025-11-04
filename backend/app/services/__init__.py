"""
Service layer for external integrations.

This module contains services for:
- Pinecone vector database operations
- OpenAI API (embeddings and chat completions)
- PostgreSQL REST API integration
- Email notifications
"""

from .pinecone_service import PineconeService
from .openai_service import OpenAIService
from .postgresql_service import PostgreSQLService
from .email_service import EmailService

__all__ = [
    "PineconeService",
    "OpenAIService",
    "PostgreSQLService",
    "EmailService",
]
