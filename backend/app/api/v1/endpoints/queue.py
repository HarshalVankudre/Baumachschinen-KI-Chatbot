"""
Upload Queue Endpoints

API endpoints for managing the server-side upload queue.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import require_superuser
from app.core.database import get_database
from app.models.user import UserModel
from app.models.upload_queue import UploadQueueModel
from app.services.upload_queue_service import get_queue_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=List[UploadQueueModel],
    summary="Get upload queue",
    description="Get all documents in the upload queue (superuser/admin only)"
)
async def get_queue(
    user: UserModel = Depends(require_superuser)
):
    """
    Get all items in the upload queue, sorted by position.

    Returns:
    - List of queue items with status, position, and progress
    """
    try:
        db = get_database()
        queue_service = get_queue_service(db)

        queue = await queue_service.get_queue()

        logger.info(f"Retrieved queue with {len(queue)} items for user {user.username}")
        return queue

    except Exception as e:
        logger.error(f"Failed to get queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=dict,
    summary="Get queue statistics",
    description="Get queue statistics (superuser/admin only)"
)
async def get_queue_stats(
    user: UserModel = Depends(require_superuser)
):
    """
    Get queue statistics.

    Returns:
    - total: Total items in queue
    - pending: Items waiting to be processed
    - processing: Items currently being processed
    - completed: Items successfully processed
    - failed: Items that failed processing
    """
    try:
        db = get_database()
        queue_service = get_queue_service(db)

        stats = await queue_service.get_queue_stats()

        logger.info(f"Retrieved queue stats for user {user.username}: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get queue stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )


@router.post(
    "/clear",
    response_model=dict,
    summary="Clear all queue items",
    description="Clear all items from the queue (useful for cleanup) (superuser/admin only)"
)
async def clear_queue(
    user: UserModel = Depends(require_superuser)
):
    """
    Clear all items from the queue and delete associated documents.

    Useful for cleaning up orphaned queue items.
    """
    try:
        db = get_database()
        queue_service = get_queue_service(db)

        # Get all queue items
        queue_items = await queue_service.get_queue()

        deleted_count = 0
        for item in queue_items:
            # Delete document metadata (if it exists)
            await db.document_metadata.delete_one({"document_id": item.document_id})

            # Delete file if exists
            import os
            if os.path.exists(item.file_path):
                try:
                    os.remove(item.file_path)
                except Exception as e:
                    logger.warning(f"Could not delete file {item.file_path}: {str(e)}")

            # Remove from queue
            await queue_service.remove_from_queue(item.queue_id)
            deleted_count += 1

        logger.info(f"User {user.username} cleared {deleted_count} items from queue")

        return {
            "success": True,
            "message": f"Cleared {deleted_count} items from queue",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        logger.error(f"Failed to clear queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue: {str(e)}"
        )


@router.delete(
    "/{queue_id}",
    response_model=dict,
    summary="Remove item from queue",
    description="Remove an item from the queue and delete associated document (superuser/admin only)"
)
async def remove_from_queue(
    queue_id: str,
    user: UserModel = Depends(require_superuser)
):
    """
    Remove an item from the queue.

    - Only pending items can be removed
    - Processing/completed items cannot be removed
    - Also deletes the associated document metadata and file
    """
    try:
        db = get_database()
        queue_service = get_queue_service(db)

        # Get the item
        item = await queue_service.get_queue_item(queue_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue item {queue_id} not found"
            )

        # Allow removing pending items
        # Also allow removing orphaned "processing" items (from old queue system before the fix)
        if item.status not in ["pending", "processing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove {item.status} items from queue. Only pending or processing items can be removed."
            )

        # Delete the associated document metadata (if it exists)
        # Note: For pending items, metadata might not exist yet
        result = await db.document_metadata.delete_one({"document_id": item.document_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted document metadata for {item.document_id}")
        else:
            logger.info(f"No document metadata found for {item.document_id} (still in queue)")

        # Delete the file if it exists
        import os
        if os.path.exists(item.file_path):
            os.remove(item.file_path)
            logger.info(f"Deleted file {item.file_path}")

        # Remove from queue
        removed = await queue_service.remove_from_queue(queue_id)

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove item from queue"
            )

        logger.info(f"User {user.username} removed {queue_id} from queue and deleted associated document")

        return {
            "success": True,
            "message": "Item removed from queue and document deleted",
            "queue_id": queue_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from queue: {str(e)}"
        )
