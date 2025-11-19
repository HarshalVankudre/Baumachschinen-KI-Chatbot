"""
Service layer for external integrations.

This module contains services for:
- Weaviate vector database operations (with hybrid search and multi-tenancy)
- OpenAI API (embeddings and chat completions)
- Email notifications
"""

from .weaviate_service import WeaviateService
from .openai_service import OpenAIService
from .email_service import EmailService

__all__ = [
    "WeaviateService",
    "OpenAIService",
    "EmailService",
]
