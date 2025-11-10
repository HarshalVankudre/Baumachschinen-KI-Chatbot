"""
Upload Queue Service

Manages the server-side upload queue for sequential document processing.
"""
import logging
import asyncio
from datetime import datetime, UTC
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.upload_queue import UploadQueueModel
from app.services.document_processor import get_document_processor
from app.services.document_events import get_document_events_manager

logger = logging.getLogger(__name__)


class UploadQueueService:
    """Service for managing upload queue"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.upload_queue
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None

    async def add_to_queue(
        self,
        document_id: str,
        filename: str,
        category: str,
        file_path: str,
        file_size_bytes: int,
        uploader_id: str,
        uploader_name: str,
    ) -> UploadQueueModel:
        """Add a document to the processing queue"""

        # Get next position in queue
        max_position = await self.collection.find_one(
            sort=[("position", -1)]
        )
        next_position = (max_position["position"] + 1) if max_position else 1

        queue_item = UploadQueueModel(
            queue_id=f"queue_{document_id}",
            document_id=document_id,
            filename=filename,
            category=category,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            uploader_id=uploader_id,
            uploader_name=uploader_name,
            status="pending",
            position=next_position,
            added_at=datetime.now(UTC),
        )

        await self.collection.insert_one(queue_item.model_dump())
        logger.info(f"Added document {document_id} to queue at position {next_position}")

        return queue_item

    async def get_queue(self) -> List[UploadQueueModel]:
        """Get all items in the queue, sorted by position"""
        cursor = self.collection.find().sort("position", 1)
        items = await cursor.to_list(length=None)
        return [UploadQueueModel(**item) for item in items]

    async def get_queue_item(self, queue_id: str) -> Optional[UploadQueueModel]:
        """Get a specific queue item"""
        item = await self.collection.find_one({"queue_id": queue_id})
        return UploadQueueModel(**item) if item else None

    async def update_queue_item(
        self,
        queue_id: str,
        updates: dict,
    ) -> bool:
        """Update a queue item"""
        result = await self.collection.update_one(
            {"queue_id": queue_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    async def remove_from_queue(self, queue_id: str) -> bool:
        """Remove an item from the queue"""
        result = await self.collection.delete_one({"queue_id": queue_id})

        if result.deleted_count > 0:
            # Reorder remaining items
            await self._reorder_queue()
            logger.info(f"Removed {queue_id} from queue")
            return True

        return False

    async def _reorder_queue(self):
        """Reorder queue positions after removal"""
        items = await self.collection.find().sort("position", 1).to_list(length=None)

        for idx, item in enumerate(items, start=1):
            if item["position"] != idx:
                await self.collection.update_one(
                    {"queue_id": item["queue_id"]},
                    {"$set": {"position": idx}}
                )

    async def _process_queue(self):
        """
        Background task that processes the queue sequentially - runs continuously.

        This is a resilient processor that:
        1. Constantly checks for pending items in the queue
        2. Takes the first pending item and removes it from queue
        3. Processes the document
        4. Immediately looks for the next item
        5. Never stops - even if individual documents fail
        """
        logger.info("Queue processor started - will run continuously until cancelled")

        while True:
            try:
                # Get next pending item (only pending, not processing)
                next_item_data = await self.collection.find_one(
                    {"status": "pending"},
                    sort=[("position", 1)]
                )

                if not next_item_data:
                    # No pending items, wait and check again
                    await asyncio.sleep(2)
                    continue

                next_item = UploadQueueModel(**next_item_data)
                logger.info(
                    f"Found pending item: {next_item.filename} (position {next_item.position}) - "
                    f"removing from queue and starting processing"
                )

                # IMMEDIATELY remove from queue when starting to process
                # This ensures upload queue only shows pending items
                await self.remove_from_queue(next_item.queue_id)
                logger.info(f"Removed {next_item.queue_id} from queue")

                # Create document metadata entry now (not during upload)
                # This prevents documents from appearing twice
                from app.models.document import DocumentMetadataModel

                document_metadata = DocumentMetadataModel(
                    document_id=next_item.document_id,
                    filename=next_item.filename,
                    category=next_item.category,
                    uploader_id=next_item.uploader_id,
                    uploader_name=next_item.uploader_name,
                    upload_date=datetime.now(UTC),
                    file_size_bytes=next_item.file_size_bytes,
                    file_extension=next_item.file_path.split('.')[-1] if '.' in next_item.file_path else '',
                    processing_status="processing",
                    chunk_count=None,
                    error_message=None,
                    deleted=False
                )

                await self.db.document_metadata.insert_one(document_metadata.model_dump())
                logger.info(f"Created document metadata for {next_item.document_id} with processing status")

                # Notify clients via SSE that processing started
                try:
                    events_manager = get_document_events_manager()
                    await events_manager.broadcast_update(
                        next_item.document_id,
                        {
                            "document_id": next_item.document_id,
                            "processing_status": "processing",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to broadcast SSE update: {str(e)}")
                    # Continue processing even if SSE fails

                # Process the document
                processor = get_document_processor()
                try:
                    logger.info(f"Starting document processing for {next_item.document_id}")
                    await processor.process_document(
                        document_id=next_item.document_id,
                        file_path=next_item.file_path,
                        category=next_item.category,
                        uploader_name=next_item.uploader_name,
                    )

                    logger.info(f"✓ Document {next_item.filename} completed successfully")

                except Exception as e:
                    logger.error(
                        f"✗ Failed to process document {next_item.filename}: {str(e)}",
                        exc_info=True
                    )

                    # Update document status to failed
                    try:
                        await self.db.document_metadata.update_one(
                            {"document_id": next_item.document_id},
                            {
                                "$set": {
                                    "processing_status": "failed",
                                    "error_message": str(e)[:500],  # Limit error message length
                                }
                            }
                        )
                    except Exception as db_error:
                        logger.error(f"Failed to update failed status: {str(db_error)}")

                # Small delay between items to avoid tight loop
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                # Server is shutting down
                logger.info("Queue processor cancelled - shutting down")
                raise

            except Exception as e:
                # Catch any unexpected errors in the loop itself
                # Log it but keep the processor running
                logger.error(
                    f"Unexpected error in queue processor loop: {str(e)}",
                    exc_info=True
                )
                # Wait before retrying to avoid tight error loop
                await asyncio.sleep(5)
                logger.info("Queue processor recovering from error, continuing...")

        logger.info("Queue processor stopped")

    async def get_queue_stats(self) -> dict:
        """
        Get queue statistics.
        Note: Queue only contains pending items. Once processing starts,
        items are removed from queue and tracked in document_metadata.
        """
        # Queue only contains pending items
        pending = await self.collection.count_documents({"status": "pending"})

        # Get processing/completed/failed counts from document_metadata
        processing = await self.db.document_metadata.count_documents({
            "processing_status": "processing",
            "deleted": False
        })
        completed = await self.db.document_metadata.count_documents({
            "processing_status": "completed",
            "deleted": False
        })
        failed = await self.db.document_metadata.count_documents({
            "processing_status": "failed",
            "deleted": False
        })

        return {
            "total": pending + processing + completed + failed,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
        }


# Global queue service instance
_queue_service: Optional[UploadQueueService] = None
_processor_task: Optional[asyncio.Task] = None


def get_queue_service(db: AsyncIOMotorDatabase) -> UploadQueueService:
    """Get or create queue service instance"""
    global _queue_service
    if _queue_service is None:
        _queue_service = UploadQueueService(db)
    return _queue_service


async def start_queue_processor(db: AsyncIOMotorDatabase) -> asyncio.Task:
    """
    Start the queue processor as a background task.
    Should be called once during app startup.
    """
    global _processor_task

    if _processor_task is not None and not _processor_task.done():
        logger.warning("Queue processor is already running")
        return _processor_task

    queue_service = get_queue_service(db)
    _processor_task = asyncio.create_task(queue_service._process_queue())
    logger.info("Queue processor task created")

    return _processor_task
