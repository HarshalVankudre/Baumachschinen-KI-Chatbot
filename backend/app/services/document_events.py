"""
Document Events Service

Manages Server-Sent Events (SSE) for real-time document processing updates.
Allows backend to push status updates to frontend without polling.
"""

import asyncio
import logging
from typing import Dict, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentEventsManager:
    """
    Manager for document processing SSE events

    Tracks active SSE connections and broadcasts document status updates
    to connected clients in real-time.
    """

    def __init__(self):
        # Map of document_id -> set of queues (one per active SSE connection)
        self._listeners: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, document_id: str) -> asyncio.Queue:
        """
        Subscribe to updates for a specific document

        Args:
            document_id: Document ID to subscribe to

        Returns:
            Queue that will receive status updates
        """
        queue = asyncio.Queue()

        async with self._lock:
            if document_id not in self._listeners:
                self._listeners[document_id] = set()
            self._listeners[document_id].add(queue)

        logger.info(f"Client subscribed to document {document_id} updates")
        return queue

    async def unsubscribe(self, document_id: str, queue: asyncio.Queue):
        """
        Unsubscribe from document updates

        Args:
            document_id: Document ID to unsubscribe from
            queue: Queue to remove
        """
        async with self._lock:
            if document_id in self._listeners:
                self._listeners[document_id].discard(queue)

                # Clean up if no more listeners
                if not self._listeners[document_id]:
                    del self._listeners[document_id]

        logger.info(f"Client unsubscribed from document {document_id} updates")

    async def broadcast_update(self, document_id: str, update: dict):
        """
        Broadcast a status update to all subscribers of a document

        Args:
            document_id: Document ID
            update: Update data to broadcast
        """
        async with self._lock:
            listeners = self._listeners.get(document_id, set())

            if not listeners:
                logger.debug(f"No listeners for document {document_id}, skipping broadcast")
                return

            # Add timestamp to update
            update['timestamp'] = datetime.utcnow().isoformat()

            logger.info(f"Broadcasting update for document {document_id} to {len(listeners)} listeners")

            # Send to all listening queues
            dead_queues = set()
            for queue in listeners:
                try:
                    # Use put_nowait to avoid blocking
                    queue.put_nowait(update)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for document {document_id}, skipping update")
                except Exception as e:
                    logger.error(f"Error broadcasting to queue: {e}")
                    dead_queues.add(queue)

            # Clean up dead queues
            for queue in dead_queues:
                self._listeners[document_id].discard(queue)

    async def broadcast_progress(
        self,
        document_id: str,
        status: str,
        step: str = None,
        progress: int = None,
        error: str = None,
        chunk_count: int = None
    ):
        """
        Convenience method to broadcast processing progress

        Args:
            document_id: Document ID
            status: Processing status (processing, completed, failed)
            step: Current processing step
            progress: Progress percentage (0-100)
            error: Error message if failed
            chunk_count: Number of chunks if completed
        """
        update = {
            'document_id': document_id,
            'processing_status': status,
        }

        if step:
            update['processing_step'] = step
        if progress is not None:
            update['processing_progress'] = progress
        if error:
            update['error_message'] = error
        if chunk_count is not None:
            update['chunk_count'] = chunk_count

        await self.broadcast_update(document_id, update)

    def get_listener_count(self, document_id: str = None) -> int:
        """
        Get number of active listeners

        Args:
            document_id: Specific document ID, or None for total count

        Returns:
            Number of active listeners
        """
        if document_id:
            return len(self._listeners.get(document_id, set()))
        else:
            return sum(len(queues) for queues in self._listeners.values())


# Singleton instance
_document_events_manager = None


def get_document_events_manager() -> DocumentEventsManager:
    """Get singleton document events manager instance"""
    global _document_events_manager
    if _document_events_manager is None:
        _document_events_manager = DocumentEventsManager()
    return _document_events_manager
