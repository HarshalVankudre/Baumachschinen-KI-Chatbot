"""
MongoDB Schema Validation for Conversations Collection (DB-005)
Defines conversation structure with embedded messages array
"""

from datetime import datetime
from typing import List, Optional

# Conversations Collection Schema Validation
CONVERSATIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "conversation_id",
            "user_id",
            "title",
            "created_at",
            "updated_at",
            "message_count",
            "messages"
        ],
        "properties": {
            "_id": {
                "bsonType": "objectId"
            },
            "conversation_id": {
                "bsonType": "string",
                "description": "UUID string (unique identifier)",
                "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
            },
            "user_id": {
                "bsonType": "string",
                "description": "User ID who owns this conversation"
            },
            "title": {
                "bsonType": "string",
                "description": "Conversation title (auto-generated or custom)",
                "maxLength": 200
            },
            "created_at": {
                "bsonType": "date",
                "description": "Conversation creation timestamp"
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Last update timestamp"
            },
            "message_count": {
                "bsonType": "int",
                "description": "Number of messages in conversation",
                "minimum": 0
            },
            "last_message_at": {
                "bsonType": ["date", "null"],
                "description": "Timestamp of last message"
            },
            "messages": {
                "bsonType": "array",
                "description": "Array of messages in conversation",
                "items": {
                    "bsonType": "object",
                    "required": ["message_id", "role", "content", "timestamp"],
                    "properties": {
                        "message_id": {
                            "bsonType": "string",
                            "description": "UUID for this message"
                        },
                        "role": {
                            "enum": ["user", "assistant"],
                            "description": "Message sender role"
                        },
                        "content": {
                            "bsonType": "string",
                            "description": "Message content",
                            "maxLength": 10000
                        },
                        "timestamp": {
                            "bsonType": "date",
                            "description": "Message timestamp"
                        },
                        "edited": {
                            "bsonType": "bool",
                            "description": "Whether message was edited"
                        },
                        "original_content": {
                            "bsonType": ["string", "null"],
                            "description": "Original content before edit"
                        },
                        "metadata": {
                            "bsonType": "object",
                            "description": "Message metadata",
                            "properties": {
                                "sources": {
                                    "bsonType": "array",
                                    "description": "Source document names",
                                    "items": {"bsonType": "string"}
                                },
                                "response_time_ms": {
                                    "bsonType": ["int", "null"],
                                    "description": "Response generation time"
                                },
                                "model_used": {
                                    "bsonType": ["string", "null"],
                                    "description": "AI model used"
                                },
                                "token_count": {
                                    "bsonType": ["int", "null"],
                                    "description": "Token count for this message"
                                },
                                "query_sources": {
                                    "bsonType": "array",
                                    "description": "Data sources queried",
                                    "items": {
                                        "enum": ["pinecone", "postgresql", "none"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def get_conversations_collection_options():
    """
    Get collection options for conversations collection

    Returns:
        Dictionary of collection options
    """
    return {
        "validator": CONVERSATIONS_SCHEMA,
        "validationLevel": "strict",
        "validationAction": "error"
    }


def get_default_conversation_document(
    conversation_id: str,
    user_id: str,
    title: str = "New Conversation"
) -> dict:
    """
    Create a default conversation document

    Args:
        conversation_id: UUID string
        user_id: Owner's user ID
        title: Conversation title

    Returns:
        Conversation document dictionary
    """
    now = datetime.utcnow()
    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
        "last_message_at": None,
        "messages": []
    }


def create_message_document(
    message_id: str,
    role: str,
    content: str,
    sources: Optional[List[str]] = None,
    response_time_ms: Optional[int] = None,
    model_used: Optional[str] = None,
    token_count: Optional[int] = None,
    query_sources: Optional[List[str]] = None
) -> dict:
    """
    Create a message document for embedding in conversation

    Args:
        message_id: UUID string
        role: 'user' or 'assistant'
        content: Message content
        sources: Source document names (for assistant messages)
        response_time_ms: Response generation time
        model_used: AI model name
        token_count: Token count
        query_sources: Data sources queried

    Returns:
        Message document dictionary
    """
    return {
        "message_id": message_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow(),
        "edited": False,
        "original_content": None,
        "metadata": {
            "sources": sources or [],
            "response_time_ms": response_time_ms,
            "model_used": model_used,
            "token_count": token_count,
            "query_sources": query_sources or []
        }
    }
