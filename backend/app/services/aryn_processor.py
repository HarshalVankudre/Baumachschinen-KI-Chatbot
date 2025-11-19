"""
Direct Aryn SDK Document Processing Service

Uses Aryn's DocParse API directly for superior document processing:
- DETR model for intelligent element detection (text, tables, images, headers)
- Built-in OCR for scanned documents
- Table structure extraction
- Image processing with bounding boxes

Then uses our existing Weaviate v4 service for vector storage.
This approach bypasses Sycamore's weaviate integration issues.
"""

import logging
import os
import time
from typing import Dict, Any, List
from datetime import datetime, timezone

from aryn_sdk.partition import partition_file, tables_to_pandas
from app.config import get_settings
from app.core.database import get_database
from app.services.document_events import get_document_events_manager
from app.services.weaviate_service import weaviate_service
from app.services.text_chunker import get_text_chunker
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
settings = get_settings()


class ArynDocumentProcessor:
    """
    Document processor using Aryn SDK directly.

    Pipeline:
    1. Use Aryn DocParse API to partition document
    2. Extract text, tables, and images from Aryn's output
    3. Chunk the content
    4. Generate embeddings and upload to Weaviate (using our existing v4 service)

    Benefits over Sycamore:
    - No weaviate-client version conflicts
    - Direct control over the pipeline
    - Uses our existing, tested Weaviate integration
    - Still gets all of Aryn's superior document processing
    """

    def __init__(self):
        """Initialize Aryn processor."""
        if not settings.aryn_api_key:
            raise ValueError(
                "ARYN_API_KEY not configured. Get your API key from: https://www.aryn.ai/"
            )

        self.db = get_database()
        self.events_manager = get_document_events_manager()
        self.weaviate_service = weaviate_service
        self.text_chunker = get_text_chunker()
        self.openai_service = OpenAIService()

        logger.info(
            f"Aryn processor initialized (Direct SDK):\n"
            f"  - Aryn DocParse API: ENABLED\n"
            f"  - DETR model: Auto-detect text, tables, images\n"
            f"  - OCR: {settings.sycamore_use_ocr}\n"
            f"  - Table extraction: {settings.sycamore_extract_tables}\n"
            f"  - Image extraction: {settings.sycamore_extract_images}\n"
            f"  - Weaviate: v4 (our existing service)\n"
            f"  ✓ No Sycamore dependencies!"
        )

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        category: str,
        uploader_name: str
    ) -> Dict[str, Any]:
        """
        Process document using Aryn SDK.

        Args:
            document_id: Unique document ID
            file_path: Path to uploaded file
            category: Document category
            uploader_name: Username of uploader

        Returns:
            Processing result with status and metadata
        """
        start_time = time.time()

        try:
            # Ensure Weaviate is connected
            if not self.weaviate_service._is_connected:
                await self.weaviate_service.connect()

            logger.info(f"[ARYN] Starting document processing for {document_id}")

            # Update status
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_status": "processing",
                    "processing_step": "partitioning",
                    "processing_progress": 0
                }}
            )

            await self.events_manager.broadcast_progress(
                document_id=document_id,
                status="processing",
                step="partitioning",
                progress=0
            )

            # Step 1: Partition document with Aryn DocParse (FULL VISION MODE)
            logger.info(
                f"[ARYN] Step 1: Calling Aryn DocParse API with VISION models...\n"
                f"  → Vision OCR: ocr_vision (most accurate)\n"
                f"  → Vision Table Extraction: vision models\n"
                f"  → DETR Model: Auto-detect elements\n"
                f"  → Image Summarization: ENABLED\n"
                f"  → Image Captions: ENABLED"
            )

            partitioned_doc = partition_file(
                file_path,
                aryn_api_key=settings.aryn_api_key,
                # Vision OCR - uses vision models for maximum accuracy
                text_mode="ocr_vision" if settings.sycamore_use_ocr else "inline",
                # Vision-based table extraction
                table_mode="vision" if settings.sycamore_extract_tables else "none",
                # Image processing with vision models
                summarize_images=True,  # Generate text summaries of images
                extract_images=settings.sycamore_extract_images,
                image_extraction_options={
                    "associate_captions": True,  # Associate captions with images
                    "extract_image_format": "PNG"  # Extract as PNG
                },
                # Threshold for DETR model element detection
                threshold="auto",  # Let Aryn optimize
                # Output format
                output_format="json"
            )

            logger.info(f"[ARYN] ✓ DocParse completed, extracting elements...")

            # Update progress
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "extracting",
                    "processing_progress": 30
                }}
            )

            # Step 2: Extract and combine all text content
            # partition_file returns a dict with 'elements' key
            elements = partitioned_doc.get("elements", [])
            text_content = self._extract_text_from_elements(elements)
            char_count = len(text_content)

            logger.info(f"[ARYN] ✓ Extracted {char_count} characters from {len(elements)} elements")

            # Update progress
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "chunking",
                    "processing_progress": 50
                }}
            )

            # Step 3: Chunk the text
            logger.info(f"[ARYN] Step 3: Chunking text...")
            chunks = self.text_chunker.chunk_text(text_content)
            chunk_count = len(chunks)

            logger.info(f"[ARYN] ✓ Created {chunk_count} chunks")

            # Update progress
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "uploading",
                    "processing_progress": 70
                }}
            )

            # Step 4: Generate embeddings
            logger.info(f"[ARYN] Step 4: Generating embeddings for {chunk_count} chunks...")
            embeddings = await self.openai_service.generate_embeddings_batch(chunks)
            logger.info(f"[ARYN] ✓ Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0]) if embeddings else 0})")

            # Step 5: Upload to Weaviate using our existing service
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "uploading",
                    "processing_progress": 80
                }}
            )

            logger.info(f"[ARYN] Step 5: Uploading to Weaviate...")

            # Create objects in Weaviate format
            objects = []
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                obj = {
                    "properties": {
                        "document_id": document_id,
                        "filename": os.path.basename(file_path),
                        "category": category,
                        "uploader_name": uploader_name,
                        "chunk_index": idx,
                        "text_content": chunk_text[:10000],  # Limit to 10k chars
                        "created_at": datetime.now(timezone.utc).isoformat()
                    },
                    "vector": embedding
                }
                objects.append(obj)

            # Batch upsert to Weaviate (no multi-tenancy - all documents shared)
            result = await self.weaviate_service.batch_upsert(
                objects=objects,
                collection_name="Documents",
                tenant=None  # Multi-tenancy disabled - all documents shared
            )

            logger.info(f"[ARYN] ✓ Uploaded {result['success']} chunks to Weaviate ({result['failed']} failed)")

            # Step 6: Update MongoDB with success
            processing_time = time.time() - start_time
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_status": "completed",
                    "processing_step": None,
                    "processing_progress": 100,
                    "chunk_count": chunk_count,
                    "processing_time_seconds": round(processing_time, 2),
                    "processor_type": "aryn"
                }}
            )

            logger.info(
                f"[ARYN] Document {document_id} processed successfully in {processing_time:.2f}s"
            )

            # Broadcast completion
            await self.events_manager.broadcast_progress(
                document_id=document_id,
                status="completed",
                progress=100,
                chunk_count=chunk_count
            )

            # Clean up temporary file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"[ARYN] Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {str(e)}")

            return {
                "status": "success",
                "document_id": document_id,
                "chunk_count": chunk_count,
                "processing_time_seconds": round(processing_time, 2),
                "processor_type": "aryn"
            }

        except Exception as e:
            # Update MongoDB with failure
            processing_time = time.time() - start_time
            error_message = str(e)

            logger.error(f"[ARYN] Document processing failed for {document_id}: {error_message}")

            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_status": "failed",
                    "error_message": error_message,
                    "processing_time_seconds": round(processing_time, 2),
                    "processor_type": "aryn"
                }}
            )

            # Broadcast failure
            await self.events_manager.broadcast_progress(
                document_id=document_id,
                status="failed",
                error=error_message
            )

            # Clean up temporary file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

            return {
                "status": "failed",
                "document_id": document_id,
                "error": error_message,
                "processor_type": "aryn"
            }

    def _extract_text_from_elements(self, elements: List[Any]) -> str:
        """
        Extract text from Aryn's partitioned elements.

        Combines text from all elements (text blocks, tables, headers, etc.)
        into a single string for chunking.

        Args:
            elements: List of Aryn element objects or dicts

        Returns:
            Combined text content
        """
        text_parts = []

        for idx, element in enumerate(elements):
            # Handle both dict and object formats
            if isinstance(element, dict):
                # Dict format
                text = element.get('text_representation') or element.get('text') or element.get('content', '')
                elem_type = element.get('type', '')

                if text:
                    text_parts.append(text)

                # For tables in dict format
                if elem_type == 'table' and element.get('table'):
                    try:
                        # Try to extract table content
                        table_data = element.get('table')
                        if isinstance(table_data, str):
                            text_parts.append(f"\n{table_data}\n")
                    except Exception as e:
                        logger.warning(f"Failed to extract table {idx}: {e}")
            else:
                # Object format
                if hasattr(element, 'text_representation') and element.text_representation:
                    text_parts.append(element.text_representation)
                elif hasattr(element, 'text') and element.text:
                    text_parts.append(element.text)
                elif hasattr(element, 'content') and element.content:
                    text_parts.append(element.content)

                # For tables, try to get structured representation
                if hasattr(element, 'type') and element.type == 'table':
                    if hasattr(element, 'table') and element.table:
                        try:
                            df = tables_to_pandas([element])[0]
                            table_text = df.to_string()
                            text_parts.append(f"\n{table_text}\n")
                        except Exception as e:
                            logger.warning(f"Failed to convert table to pandas: {e}")

        combined_text = "\n\n".join(filter(None, text_parts))

        # Debug logging
        if not combined_text and elements:
            logger.warning(
                f"[ARYN] No text extracted from {len(elements)} elements. "
                f"Sample element structure: {elements[0] if elements else 'N/A'}"
            )

        return combined_text


# Singleton instance
_aryn_processor = None


def get_aryn_processor() -> ArynDocumentProcessor:
    """Get singleton Aryn processor instance."""
    global _aryn_processor
    if _aryn_processor is None:
        _aryn_processor = ArynDocumentProcessor()
    return _aryn_processor
