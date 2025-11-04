"""
Chat Endpoints

Handles conversation management and chat interactions:
- Create conversation (POST /api/chat/conversations)
- List conversations (GET /api/chat/conversations)
- Get conversation (GET /api/chat/conversations/{id})
- Update conversation (PUT /api/chat/conversations/{id})
- Delete conversation (DELETE /api/chat/conversations/{id})
- Send message with streaming (POST /api/chat/conversations/{id}/messages)
- Export conversation (GET /api/chat/conversations/{id}/export)
"""

import logging
import time
import json
from datetime import datetime, UTC
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_database
from app.models.user import UserModel
from app.models.conversation import ConversationModel, MessageModel
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
)
from app.api.v1.dependencies import get_current_user
from app.services.openai_service import get_openai_service
from app.services.pinecone_service import get_pinecone_service
from app.services.postgresql_service import get_postgresql_service
from app.utils.security import generate_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", status_code=status.HTTP_201_CREATED, response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    user: UserModel = Depends(get_current_user)
) -> ConversationResponse:
    """
    Create a new conversation

    Creates an empty conversation with optional title.
    First message should be sent via POST /conversations/{id}/messages endpoint.
    """
    try:
        db = get_database()

        # Generate auto-title if not provided
        title = conversation_data.title or "New Conversation"

        # Create conversation
        conversation = ConversationModel(
            conversation_id=generate_token(),
            user_id=user.user_id,
            title=title,
            messages=[],
            message_count=0
        )

        # Save to database
        await db.conversations.insert_one(conversation.model_dump())

        logger.info(f"Conversation created: {conversation.conversation_id} by {user.username}")

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title,
            message_count=0,
            last_message_at=conversation.created_at,
            created_at=conversation.created_at,
            messages=[]
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user: UserModel = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100, description="Max conversations to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    search: Optional[str] = Query(default=None, description="Search by title or content")
) -> ConversationListResponse:
    """
    List user's conversations

    Returns conversations ordered by last_message_at (most recent first).
    Supports pagination and search.
    """
    try:
        db = get_database()

        # Build query filter
        filter_query = {
            "user_id": user.user_id,
            "deleted": False
        }

        # Add search filter if provided
        if search:
            filter_query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"messages.content": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await db.conversations.count_documents(filter_query)

        # Get conversations with pagination
        conversations_cursor = db.conversations.find(filter_query)\
            .sort("last_message_at", -1)\
            .skip(offset)\
            .limit(limit)

        conversations_list = []
        async for conv_doc in conversations_cursor:
            conv = ConversationModel(**conv_doc)
            conversations_list.append(
                ConversationResponse(
                    conversation_id=conv.conversation_id,
                    user_id=conv.user_id,
                    title=conv.title,
                    message_count=conv.message_count,
                    last_message_at=conv.last_message_at,
                    created_at=conv.created_at,
                    messages=None  # Don't include full messages in list view
                )
            )

        logger.info(f"Listed {len(conversations_list)} conversations for {user.username}")

        return ConversationListResponse(
            conversations=conversations_list,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: UserModel = Depends(get_current_user)
) -> ConversationResponse:
    """
    Get a single conversation with all messages

    Returns full conversation details including all messages.
    User must own the conversation.
    """
    try:
        db = get_database()

        # Find conversation
        conv_doc = await db.conversations.find_one({
            "conversation_id": conversation_id,
            "deleted": False
        })

        if not conv_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        conv = ConversationModel(**conv_doc)

        # Verify ownership
        if conv.user_id != user.user_id:
            logger.warning(f"User {user.username} attempted to access conversation {conversation_id} owned by {conv.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this conversation"
            )

        # Convert messages to response format
        messages_response = [
            MessageResponse(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
                is_edited=msg.is_edited
            )
            for msg in conv.messages
        ]

        return ConversationResponse(
            conversation_id=conv.conversation_id,
            user_id=conv.user_id,
            title=conv.title,
            message_count=conv.message_count,
            last_message_at=conv.last_message_at,
            created_at=conv.created_at,
            messages=messages_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    user: UserModel = Depends(get_current_user)
) -> ConversationResponse:
    """
    Update conversation title

    User must own the conversation.
    """
    try:
        db = get_database()

        # Find and verify ownership
        conv_doc = await db.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user.user_id,
            "deleted": False
        })

        if not conv_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Update title
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$set": {"title": update_data.title}}
        )

        logger.info(f"Conversation {conversation_id} title updated by {user.username}")

        # Get updated conversation
        updated_doc = await db.conversations.find_one({"conversation_id": conversation_id})
        conv = ConversationModel(**updated_doc)

        return ConversationResponse(
            conversation_id=conv.conversation_id,
            user_id=conv.user_id,
            title=conv.title,
            message_count=conv.message_count,
            last_message_at=conv.last_message_at,
            created_at=conv.created_at,
            messages=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user: UserModel = Depends(get_current_user)
):
    """
    Delete conversation (soft delete)

    Sets deleted=true rather than actually removing the document.
    User must own the conversation.
    """
    try:
        db = get_database()

        # Find and verify ownership
        conv_doc = await db.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user.user_id,
            "deleted": False
        })

        if not conv_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Soft delete
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "deleted": True,
                    "deleted_at": datetime.now(UTC)
                }
            }
        )

        logger.info(f"Conversation {conversation_id} deleted by {user.username}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    user: UserModel = Depends(get_current_user)
):
    """
    Export conversation as markdown file

    Returns downloadable markdown file with conversation history.
    User must own the conversation.
    """
    try:
        db = get_database()

        # Find and verify ownership
        conv_doc = await db.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user.user_id,
            "deleted": False
        })

        if not conv_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        conv = ConversationModel(**conv_doc)

        # Generate markdown content
        markdown_lines = [
            f"# {conv.title}",
            f"",
            f"**Created:** {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Last Updated:** {conv.last_message_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Messages:** {conv.message_count}",
            f"",
            "---",
            f""
        ]

        for msg in conv.messages:
            role_label = "You" if msg.role == "user" else "Assistant"
            timestamp_str = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')

            markdown_lines.append(f"### {role_label} ({timestamp_str})")
            markdown_lines.append("")
            markdown_lines.append(msg.content)
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

        markdown_content = "\n".join(markdown_lines)

        # Return as downloadable file
        filename = f"conversation_{conversation_id}.md"

        logger.info(f"Exported conversation {conversation_id} for {user.username}")

        return StreamingResponse(
            iter([markdown_content]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export conversation"
        )




@router.post("/conversations/{conversation_id}/messages")
async def send_message_streaming(
    conversation_id: str,
    message_data: MessageCreate,
    user: UserModel = Depends(get_current_user)
):
    """
    Send message and receive streaming AI response via SSE

    This is the CORE FEATURE of the chatbot:
    1. Saves user message to conversation
    2. Classifies query and retrieves context from Pinecone/PostgreSQL
    3. Streams AI response token-by-token using Server-Sent Events
    4. Saves AI response to conversation
    5. Returns source citations and metadata

    SSE Event Types:
    - token: Partial response content
    - source: Citation information
    - complete: Final metadata (message_id, tokens, response_time)
    - error: Error information

    User must own the conversation (403 if not).
    """
    from app.services.ai_agent import get_ai_agent

    async def stream_response():
        """Generator function for SSE streaming"""
        start_time = time.time()
        db = get_database()
        ai_agent = None
        full_response = ""
        sources = []
        category = None

        try:
            # Step 1: Verify conversation ownership
            conv_doc = await db.conversations.find_one({
                "conversation_id": conversation_id,
                "deleted": False
            })

            if not conv_doc:
                yield json.dumps({"type": "error", "message": "Conversation not found"})
                return

            conv = ConversationModel(**conv_doc)

            if conv.user_id != user.user_id:
                logger.warning(f"User {user.username} attempted to access conversation {conversation_id}")
                yield json.dumps({"type": "error", "message": "Access denied"})
                return

            # Step 2: Save user message
            user_msg = MessageModel(
                message_id=generate_token(),
                role="user",
                content=message_data.message,
                timestamp=datetime.now(UTC)
            )

            await db.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": user_msg.model_dump()},
                    "$inc": {"message_count": 1},
                    "$set": {"last_message_at": datetime.now(UTC)}
                }
            )

            logger.info(f"User message saved to conversation {conversation_id}")

            # Step 3: Get conversation history for context
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in conv.messages[-5:]  # Last 5 messages
            ]

            # Step 4: Initialize AI agent and classify query
            ai_agent = get_ai_agent()
            category = await ai_agent.classify_query(message_data.message)

            # Step 5: Handle based on category
            context = ""
            sources = []

            # CONVERSATIONAL queries: Skip database search entirely
            if category == "conversational":
                logger.info(f"[CONVERSATIONAL] Skipping database search for conversational query: {message_data.message[:50]}...")
                # No database retrieval needed for greetings/small talk
                # context remains empty, sources remains empty

            # TECHNICAL queries: Search databases
            else:
                logger.info(f"[TECHNICAL] Performing database search for category: {category}")
                pinecone_results = None
                postgresql_results = None

                if category in ["documentation", "combined"]:
                    pinecone_results = await ai_agent.retrieve_from_pinecone(message_data.message)

                if category in ["machinery_specs", "combined"]:
                    postgresql_results = await ai_agent.retrieve_from_postgresql(
                        message_data.message,
                        user.authorization_level
                    )

                # Step 6: Aggregate context
                context, sources = await ai_agent.aggregate_context(
                    query=message_data.message,
                    pinecone_results=pinecone_results,
                    postgresql_results=postgresql_results
                )

            # Step 7: Stream AI response (pass category for mode selection)
            async for token in ai_agent.generate_response_stream(
                query=message_data.message,
                context=context,
                conversation_history=conversation_history,
                category=category  # Pass category to enable conversational mode
            ):
                full_response += token
                yield json.dumps({"type": "token", "content": token})

            # Step 8: Send source citations
            if sources:
                yield json.dumps({"type": "source", "sources": sources})

            # Step 9: Calculate response time and token count
            response_time_ms = int((time.time() - start_time) * 1000)

            # Count tokens (different for conversational vs technical)
            if category == "conversational":
                messages_for_count = [
                    {"role": "system", "content": ai_agent.SYSTEM_PROMPT_CONVERSATIONAL},
                    {"role": "user", "content": message_data.message},
                    {"role": "assistant", "content": full_response}
                ]
            else:
                messages_for_count = [
                    {"role": "system", "content": ai_agent.SYSTEM_PROMPT_TECHNICAL},
                    {"role": "user", "content": f"{context}\n\n{message_data.message}"},
                    {"role": "assistant", "content": full_response}
                ]
            token_count = ai_agent.openai_service.count_tokens_messages(messages_for_count)

            # Step 10: Save AI response to conversation
            ai_msg = MessageModel(
                message_id=generate_token(),
                role="assistant",
                content=full_response,
                timestamp=datetime.now(UTC),
                metadata={
                    "sources": sources,
                    "token_count": token_count,
                    "response_time_ms": response_time_ms,
                    "category": category,
                    "model": ai_agent.openai_service.chat_model
                }
            )

            await db.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": ai_msg.model_dump()},
                    "$inc": {"message_count": 1},
                    "$set": {"last_message_at": datetime.now(UTC)}
                }
            )

            logger.info(
                f"AI response saved to conversation {conversation_id} "
                f"(tokens: {token_count}, time: {response_time_ms}ms)"
            )

            # Step 11: Send completion event
            yield json.dumps({"type": "complete", "message_id": ai_msg.message_id, "token_count": token_count, "response_time_ms": response_time_ms, "sources": sources})

            # Log high token usage
            if token_count > 3000:
                logger.warning(f"High token usage in conversation {conversation_id}: {token_count} tokens")

        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}", exc_info=True)
            error_message = "An error occurred while generating the response"

            # Send error event
            yield json.dumps({"type": "error", "message": error_message, "details": str(e)})

    # Return SSE stream
    return EventSourceResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
