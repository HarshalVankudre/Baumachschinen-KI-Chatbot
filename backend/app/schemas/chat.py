"""Chat schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Message creation request schema."""
    message: str = Field(max_length=2000, description="User message (max 2000 characters)")
    edited_message_id: Optional[str] = Field(default=None, description="Message ID to edit (regenerate from)")


class MessageResponse(BaseModel):
    """Message response schema."""
    message_id: str = Field(description="Message ID")
    role: Literal['user', 'assistant'] = Field(description="Message role")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata (sources, tokens, etc.)")
    is_edited: bool = Field(default=False, description="Whether message was edited")


class ConversationCreate(BaseModel):
    """Conversation creation request schema."""
    title: Optional[str] = Field(default=None, max_length=200, description="Conversation title")


class ConversationUpdate(BaseModel):
    """Conversation update request schema."""
    title: str = Field(max_length=200, description="New conversation title")


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    conversation_id: str = Field(description="Conversation ID")
    user_id: str = Field(description="User ID who owns this conversation")
    title: str = Field(description="Conversation title")
    message_count: int = Field(description="Number of messages in conversation")
    last_message_at: datetime = Field(description="Timestamp of last message")
    created_at: datetime = Field(description="Conversation creation timestamp")
    messages: Optional[List[MessageResponse]] = Field(default=None, description="List of messages (if requested)")


class ConversationListResponse(BaseModel):
    """List of conversations response schema."""
    conversations: List[ConversationResponse] = Field(description="List of conversations")
    total: int = Field(description="Total number of conversations")
    limit: int = Field(description="Limit used in query")
    offset: int = Field(description="Offset used in query")


class StreamEvent(BaseModel):
    """Server-sent event for streaming responses."""
    event: Literal['token', 'source', 'complete', 'error'] = Field(description="Event type")
    data: Any = Field(description="Event data")


class StreamTokenEvent(BaseModel):
    """Token event data."""
    content: str = Field(description="Token content")


class StreamSourceEvent(BaseModel):
    """Source citation event data."""
    source_type: Literal['pinecone', 'postgresql', 'model_knowledge'] = Field(description="Source type")
    source_name: Optional[str] = Field(default=None, description="Source name (document, table, etc.)")
    content: Optional[str] = Field(default=None, description="Source content excerpt")


class StreamCompleteEvent(BaseModel):
    """Completion event data."""
    message_id: str = Field(description="Saved message ID")
    token_count: int = Field(description="Total tokens used")
    response_time_ms: int = Field(description="Response time in milliseconds")
    sources_used: List[str] = Field(description="List of sources used")


class StreamErrorEvent(BaseModel):
    """Error event data."""
    error_type: str = Field(description="Error type")
    error_message: str = Field(description="Error message")
