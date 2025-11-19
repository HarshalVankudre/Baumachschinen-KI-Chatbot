"""
Conversation State Management Service

Tracks conversation state across turns to enable:
- Reference resolution ("das", "die Maschine", etc.)
- Entity memory (remember discussed machines, manufacturers, components)
- Context continuity for natural conversations
- Turn tracking and conversation history

This service enables the AI agent to understand context like:
- "Wie schwer ist das?" → "Wie schwer ist der Caterpillar 320D?"
- "Zeig mir mehr davon" → "Zeig mir mehr Caterpillar Bagger"

Key Features:
- Track mentioned entities across conversation turns
- Resolve pronouns and references using conversation history
- Maintain conversation topics and intent flow
- Provide context summaries for debugging and analysis

Thread-safe singleton pattern using lru_cache for FastAPI compatibility.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    """
    Track conversation state across turns

    Enables:
    - Reference resolution ("das", "die Maschine")
    - Entity memory (remember discussed machines)
    - Context continuity
    """

    conversation_id: str
    current_topic: Optional[str] = None
    mentioned_entities: Dict[str, List[str]] = Field(default_factory=dict)
    last_intent: Optional[str] = None
    last_query: Optional[str] = None
    turn_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class ConversationStateManager:
    """
    Manage conversation state and context

    Provides:
    - State creation and retrieval
    - Entity tracking across turns
    - Reference resolution (pronouns → entities)
    - Context summarization
    - Thread-safe operations with async lock
    """

    def __init__(self):
        """Initialize conversation state manager with thread safety."""
        self.active_conversations: Dict[str, ConversationState] = {}
        self._lock = asyncio.Lock()  # Thread-safe async lock
        logger.info("ConversationStateManager initialized with thread safety")

    async def get_or_create_state(self, conversation_id: str) -> ConversationState:
        """
        Get existing state or create new one (thread-safe)

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            ConversationState for this conversation
        """
        async with self._lock:  # Thread-safe access
            if conversation_id not in self.active_conversations:
                self.active_conversations[conversation_id] = ConversationState(
                    conversation_id=conversation_id
                )
                logger.info(f"Created new conversation state: {conversation_id}")
            return self.active_conversations[conversation_id]

    async def update_state(
        self,
        conversation_id: str,
        query: str,
        intent: str,
        entities: List[Dict[str, str]]
    ) -> ConversationState:
        """
        Update conversation state with new turn (thread-safe)

        Args:
            conversation_id: Unique conversation identifier
            query: Current user query
            intent: Detected intent for this query
            entities: List of entities extracted from query
                     Format: [{"type": "machine_model", "value": "CAT 320D"}, ...]

        Returns:
            Updated ConversationState
        """
        async with self._lock:  # Thread-safe access
            # Don't call get_or_create_state - directly access dict to avoid deadlock
            if conversation_id not in self.active_conversations:
                self.active_conversations[conversation_id] = ConversationState(
                    conversation_id=conversation_id
                )
            state = self.active_conversations[conversation_id]

            # Update basic info
            state.last_query = query
            state.last_intent = intent
            state.current_topic = intent
            state.turn_count += 1
            state.updated_at = datetime.now()

            # Track entities
            for entity in entities:
                entity_type = entity.get("type")
                entity_value = entity.get("value")

                if entity_type and entity_value:
                    if entity_type not in state.mentioned_entities:
                        state.mentioned_entities[entity_type] = []

                    # Add if not already present
                    if entity_value not in state.mentioned_entities[entity_type]:
                        state.mentioned_entities[entity_type].append(entity_value)
                        logger.debug(
                            f"Conversation {conversation_id}: Tracked entity "
                            f"{entity_type}={entity_value}"
                        )

            logger.info(
                f"Conversation {conversation_id}: Turn {state.turn_count}, "
                f"Intent: {intent}, Entities: {len(entities)}"
            )

            return state

    async def resolve_references(self, query: str, conversation_id: str) -> str:
        """
        Resolve pronouns and references using conversation history (thread-safe read)

        This method makes conversations feel more natural by understanding
        context. Users can say "das" or "die Maschine" and the system
        will understand which machine they're referring to.

        Args:
            query: Current query potentially containing references
            conversation_id: Conversation ID to get state from

        Returns:
            Query with references resolved to actual entities

        Examples:
            - "Wie schwer ist das?" → "Wie schwer ist der Caterpillar 320D?"
            - "Zeig mir mehr davon" → "Zeig mir mehr Caterpillar Bagger"
            - "Was kostet die Maschine?" → "Was kostet die CAT 320D?"
        """
        async with self._lock:
            if conversation_id not in self.active_conversations:
                return query  # No state to resolve from

            state = self.active_conversations[conversation_id]
            resolved_query = query

            # References to resolve with priority order for entity types
            references = {
                "das": ["machine_model", "manufacturer", "component"],
                "die maschine": ["machine_model"],
                "der": ["machine_model", "manufacturer"],
                "davon": ["machine_model", "task", "category"],
                "diese": ["machine_model", "manufacturer"],
                "dieser": ["machine_model", "manufacturer"],
                "dieses": ["machine_model", "component"],
            }

            query_lower = query.lower()

            for ref, entity_types in references.items():
                if ref in query_lower:
                    # Find most recent entity of matching type
                    for entity_type in entity_types:
                        if entity_type in state.mentioned_entities:
                            entities = state.mentioned_entities[entity_type]
                            if entities:
                                last_entity = entities[-1]
                                # Replace reference with actual entity
                                resolved_query = resolved_query.replace(ref, last_entity)
                                logger.info(
                                    f"Resolved reference '{ref}' → '{last_entity}' "
                                    f"(type: {entity_type})"
                                )
                                break

            return resolved_query

    def get_context_summary(self, state: ConversationState) -> str:
        """
        Get summary of conversation context

        Args:
            state: Conversation state to summarize

        Returns:
            Human-readable summary of conversation context

        Example output:
            ```
            Aktuelles Thema: search
            Erwähnte Entitäten:
              - machine_model: CAT 320D, Komatsu PC200
              - manufacturer: Caterpillar
              - specification: Gewicht, Leistung
            ```
        """
        if state.turn_count == 0:
            return "Neue Konversation"

        context_parts = [
            f"Aktuelles Thema: {state.current_topic or 'Unbekannt'}",
        ]

        if state.mentioned_entities:
            context_parts.append("Erwähnte Entitäten:")
            for entity_type, entities in state.mentioned_entities.items():
                # Show last 3 entities of each type
                recent_entities = entities[-3:]
                context_parts.append(f"  - {entity_type}: {', '.join(recent_entities)}")

        return "\n".join(context_parts)

    async def clear_state(self, conversation_id: str) -> bool:
        """
        Clear conversation state (thread-safe)

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if state was cleared, False if conversation didn't exist
        """
        async with self._lock:  # Thread-safe access
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
                logger.info(f"Cleared conversation state: {conversation_id}")
                return True
            return False

    async def get_all_conversations(self) -> List[str]:
        """
        Get list of all active conversation IDs (thread-safe)

        Returns:
            List of conversation IDs
        """
        async with self._lock:
            return list(self.active_conversations.keys())

    async def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """
        Remove conversations older than max_age_hours to prevent memory leaks (thread-safe)

        This method should be called periodically (e.g., via a background task)
        to clean up stale conversations and prevent unbounded memory growth.

        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 24)

        Returns:
            Number of conversations removed

        Example:
            >>> manager = get_conversation_manager()
            >>> removed = await manager.cleanup_old_conversations(max_age_hours=12)
            >>> print(f"Cleaned up {removed} conversations")
        """
        async with self._lock:  # Thread-safe access
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            to_remove = []

            for conv_id, state in self.active_conversations.items():
                if state.updated_at < cutoff_time:
                    to_remove.append(conv_id)

            # Remove old conversations
            for conv_id in to_remove:
                del self.active_conversations[conv_id]

            if to_remove:
                logger.info(
                    f"Cleaned up {len(to_remove)} old conversations "
                    f"(older than {max_age_hours}h)"
                )

            return len(to_remove)

    async def get_conversation_count(self) -> int:
        """
        Get total number of active conversations (thread-safe).

        Returns:
            Number of active conversations in memory

        Example:
            >>> manager = get_conversation_manager()
            >>> count = await manager.get_conversation_count()
            >>> print(f"Active conversations: {count}")
        """
        async with self._lock:
            return len(self.active_conversations)

    async def cleanup_if_needed(self, max_conversations: int = 10000) -> None:
        """
        Auto-cleanup if conversation count exceeds threshold.

        This is a safety mechanism to prevent out-of-memory issues
        if cleanup_old_conversations() is not called regularly.

        Args:
            max_conversations: Maximum conversations before forcing cleanup

        Example:
            >>> manager = get_conversation_manager()
            >>> # Call this before creating new conversations
            >>> await manager.cleanup_if_needed(max_conversations=5000)
        """
        if len(self.active_conversations) > max_conversations:
            logger.warning(
                f"Conversation count ({len(self.active_conversations)}) "
                f"exceeds threshold ({max_conversations}), forcing cleanup"
            )
            await self.cleanup_old_conversations(max_age_hours=12)


# Factory function with dependency injection (thread-safe)
@lru_cache()
def get_conversation_manager() -> ConversationStateManager:
    """
    Get ConversationStateManager instance

    Returns:
        Singleton ConversationStateManager instance (thread-safe)
    """
    return ConversationStateManager()
