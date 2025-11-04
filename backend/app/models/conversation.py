"""Conversation and message models for MongoDB."""
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MessageModel(BaseModel):
    """Message model."""
    message_id: str = Field(description="Unique message ID")
    role: str = Field(description="Message role: user or assistant")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata")
    is_edited: bool = Field(default=False, description="Whether message was edited")
    edited_from: Optional[str] = Field(default=None, description="Original message ID if edited")


class ConversationModel(BaseModel):
    """Conversation document model for MongoDB."""
    conversation_id: str = Field(description="Unique conversation ID")
    user_id: str = Field(description="Owner user ID")
    title: str = Field(default="New Conversation", description="Conversation title")
    messages: List[MessageModel] = Field(default_factory=list, description="List of messages")
    message_count: int = Field(default=0, description="Number of messages")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation timestamp")
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last message timestamp")
    deleted: bool = Field(default=False, description="Soft delete flag")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user-123",
                "title": "Equipment Specifications",
                "message_count": 5,
                "created_at": "2025-01-01T00:00:00Z",
                "last_message_at": "2025-01-01T01:00:00Z",
            }
        }
    )
