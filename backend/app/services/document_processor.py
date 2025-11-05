"""
Document Processing Service

Handles document processing workflow:
- OCR extraction with Docling
- Text chunking with semantic boundaries
- Embedding generation with OpenAI
- Vector storage in Pinecone
- MongoDB status updates
"""

import logging
import os
import time
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Fix PIL DecompressionBombWarning for large PDF images
# PDFs converted to high-resolution images can exceed PIL's default 89MP limit
# Increase to 200MP to handle large technical diagrams/flowcharts
from PIL import Image
Image.MAX_IMAGE_PIXELS = 200_000_000  # 200 megapixels (was 89 MP by default)

# Document processing libraries
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        EasyOcrOptions,
        TableFormerMode,
        PictureDescriptionApiOptions
    )
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
    from docling.datamodel.settings import settings as docling_settings
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available. Document processing will be limited.")

# Text processing
import tiktoken

from app.config import get_settings
from app.core.database import get_database
from app.services.openai_service import get_openai_service
from app.services.pinecone_service import get_pinecone_service
from app.services.document_events import get_document_events_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentProcessor:
    """Service for processing uploaded documents"""

    def __init__(self):
        """Initialize document processor with service dependencies"""
        self.openai_service = get_openai_service()
        self.pinecone_service = get_pinecone_service()
        self.db = get_database()
        self.events_manager = get_document_events_manager()

        # Initialize tokenizer for chunking
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4-turbo-preview")
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        # Initialize Docling converter with advanced optimization if available
        if DOCLING_AVAILABLE:
            # Suppress PyTorch pin_memory warning when no GPU is available
            warnings.filterwarnings("ignore", message=".*pin_memory.*no accelerator.*")

            # Configure CPU optimization - use all available cores
            import multiprocessing
            num_cores = multiprocessing.cpu_count()

            logger.info(f"Configuring Docling with {num_cores} CPU cores for maximum performance")

            # Configure accelerator options for maximum CPU utilization
            accelerator_options = AcceleratorOptions(
                num_threads=num_cores,  # Use all CPU cores
                device=AcceleratorDevice.CPU  # Force CPU (works on all systems)
            )

            # Configure advanced OCR options for better quality
            ocr_options = EasyOcrOptions(
                force_full_page_ocr=True,  # Full page OCR for maximum quality
                use_gpu=False,  # Use CPU (GPU requires specific setup)
            )

            # Configure GPT-4 Vision API for chart/diagram/flowchart extraction
            # Get OpenAI API key from settings
            openai_api_key = settings.openai_api_key

            if not openai_api_key:
                raise ValueError("OpenAI API key not configured in settings")

            gpt4_vision_options = PictureDescriptionApiOptions(
                url="https://api.openai.com/v1/chat/completions",
                params=dict(
                    model="gpt-4.1-2025-04-14",  # Latest GPT-4 with vision (gpt-4o or gpt-4-turbo)
                    max_tokens=8192,  # Increased to 8192 for very detailed extraction (GPT-4o supports up to 16K)
                ),
                headers={
                    "Authorization": f"Bearer {openai_api_key}"
                },
                prompt=(
                    "Extrahiere ALLE Informationen aus diesem Bild mit MAXIMALER Detailgenauigkeit:\n\n"
                    "1. TEXTEXTRAKTION: Lese und transkribiere JEDES sichtbare Textzeichen, einschließlich:\n"
                    "   - Alle Überschriften, Beschriftungen, Bildunterschriften und Anmerkungen\n"
                    "   - Zahlen, Werte, Einheiten und Messungen\n"
                    "   - Legenden, Schlüssel und Fußnoten\n\n"
                    "2. DIAGRAMME & GRAPHEN: Falls vorhanden, beschreibe:\n"
                    "   - Diagrammtyp (Balken-, Linien-, Kreis-, Streudiagramm usw.)\n"
                    "   - Achsenbeschriftungen, Einheiten und Skalenbereiche\n"
                    "   - ALLE Datenpunkte und ihre exakten Werte\n"
                    "   - Gezeigte Trends, Muster und Beziehungen\n\n"
                    "3. TABELLEN: Falls vorhanden, extrahiere:\n"
                    "   - Spaltenüberschriften und Zeilenbeschriftungen\n"
                    "   - JEDEN Zellenwert in strukturiertem Format\n"
                    "   - Alle Summen, Zwischensummen oder Berechnungen\n\n"
                    "4. DIAGRAMME & FLUSSDIAGRAMME: Falls vorhanden, beschreibe:\n"
                    "   - Alle Formen, Kästchen und deren Textinhalt\n"
                    "   - Pfeile, Verbindungen und Flussrichtung\n"
                    "   - Prozessschritte und Entscheidungspunkte\n"
                    "   - Beziehungen zwischen Komponenten\n\n"
                    "5. TECHNISCHER INHALT: Beinhalte:\n"
                    "   - Formeln, Gleichungen und mathematische Ausdrücke\n"
                    "   - Symbole, Notationen und Fachbegriffe\n"
                    "   - Messungen, Spezifikationen und Parameter\n\n"
                    "Sei umfassend und präzise. Fasse NICHTS zusammen - extrahiere ALLES auf Deutsch."
                ),
                scale=3.0,  # Maximum quality image processing (3x resolution)
                timeout=600,  # 10 minutes per image for very large/complex documents
                batch_size=2,  # Process 2 images at a time (GPT-4 API rate limit consideration)
            )

            # Configure PDF pipeline with advanced options
            pipeline_options = PdfPipelineOptions(
                accelerator_options=accelerator_options,
                do_ocr=True,  # Enable OCR for text (GPT-4 Vision also has OCR, but traditional OCR is faster for pure text)
                do_table_structure=True,  # Enable table extraction
                do_picture_description=True,  # Enable GPT-4 Vision for charts/diagrams/flowcharts
                ocr_options=ocr_options,
                picture_description_options=gpt4_vision_options,  # GPT-4 Vision API
                generate_page_images=False,  # Don't generate full page images (saves memory)
                generate_picture_images=True,  # Generate images for GPT-4 Vision processing
                images_scale=3.0,  # Maximum quality (3x scale) for GPT-4 Vision
            )

            # Enable remote services for API-based vision models
            pipeline_options.enable_remote_services = True

            # Configure table extraction for ACCURATE mode (better quality)
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.table_structure_options.do_cell_matching = True

            # Enable pipeline profiling for performance monitoring
            docling_settings.debug.profile_pipeline_timings = True

            # Create converter with optimized configuration
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )

            logger.info(
                f"Docling DocumentConverter initialized with:\n"
                f"  - CPU cores: {num_cores}\n"
                f"  - Full page OCR: Enabled (EasyOCR)\n"
                f"  - Table extraction: ACCURATE mode\n"
                f"  - Image scale: 3.0x for maximum quality\n"
                f"  - Vision AI: GPT-4o (OpenAI API) for charts/diagrams/flowcharts\n"
                f"  - GPT-4 max tokens: 8192 (detailed extraction)\n"
                f"  - GPT-4 timeout: 600s (10 min per image)\n"
                f"  - PIL image limit: 200MP (handles large diagrams)\n"
                f"  - Remote services: ENABLED for API-based vision models\n"
                f"  - Comprehensive extraction: ALL text, tables, charts, diagrams, and technical content"
            )
        else:
            self.converter = None
            logger.warning("Docling not available - using fallback text extraction")

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        category: str,
        uploader_name: str
    ) -> Dict[str, Any]:
        """
        Process document end-to-end

        Steps:
        1. Extract text with Docling OCR
        2. Chunk text into ~500 token segments
        3. Generate embeddings for each chunk
        4. Store vectors in Pinecone
        5. Update MongoDB with completion status

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
            logger.info(f"Starting document processing for {document_id}")

            # Update status to processing
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_status": "processing",
                    "processing_step": "extracting_text",
                    "processing_progress": 0
                }}
            )

            # Broadcast processing started
            await self.events_manager.broadcast_progress(
                document_id=document_id,
                status="processing",
                step="extracting_text",
                progress=0
            )

            # Step 1: Extract text from document with progress heartbeat
            logger.info(f"Extracting text from {file_path}")

            # Use progress-aware extraction for better UX during long OCR operations
            try:
                text_content = await self._extract_text_with_progress(file_path, document_id)
            except Exception as e:
                # Fall back to standard extraction with fallback methods
                logger.warning(f"Progress-aware extraction failed, using fallback: {str(e)}")
                text_content = await self._extract_text(file_path)

            if not text_content or len(text_content.strip()) < 10:
                raise ValueError("No text content extracted from document")

            logger.info(f"Extracted {len(text_content)} characters from document")

            # Update progress after extraction
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "chunking",
                    "processing_progress": 30
                }}
            )

            # Step 2: Chunk text into segments
            logger.info("Chunking text into segments")
            chunks = self._chunk_text(text_content, chunk_size=500, overlap=50)
            logger.info(f"Created {len(chunks)} chunks from document")

            # Update progress after chunking
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "generating_embeddings",
                    "processing_progress": 50
                }}
            )

            if not chunks:
                raise ValueError("No chunks created from document text")

            # Step 3: Generate embeddings for chunks (batch processing)
            logger.info("Generating embeddings for chunks")
            embeddings = await self._generate_embeddings_batch(chunks)

            # Update progress after embeddings
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {"$set": {
                    "processing_step": "storing_vectors",
                    "processing_progress": 80
                }}
            )

            # Step 4: Store vectors in Pinecone
            logger.info("Storing vectors in Pinecone")
            filename = os.path.basename(file_path)
            await self._store_vectors(
                document_id=document_id,
                filename=filename,
                category=category,
                uploader_name=uploader_name,
                chunks=chunks,
                embeddings=embeddings
            )

            # Step 5: Update MongoDB with success
            processing_time = time.time() - start_time
            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "processing_status": "completed",
                        "chunk_count": len(chunks),
                        "processing_time_seconds": round(processing_time, 2)
                    }
                }
            )

            logger.info(
                f"Document {document_id} processed successfully in {processing_time:.2f}s "
                f"({len(chunks)} chunks)"
            )

            # Broadcast completion
            await self.events_manager.broadcast_progress(
                document_id=document_id,
                status="completed",
                progress=100,
                chunk_count=len(chunks)
            )

            # Clean up temporary file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {str(e)}")

            return {
                "status": "success",
                "document_id": document_id,
                "chunk_count": len(chunks),
                "processing_time_seconds": round(processing_time, 2)
            }

        except Exception as e:
            # Update MongoDB with failure
            processing_time = time.time() - start_time
            error_message = str(e)

            logger.error(f"Document processing failed for {document_id}: {error_message}")

            await self.db.document_metadata.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "processing_status": "failed",
                        "error_message": error_message,
                        "processing_time_seconds": round(processing_time, 2)
                    }
                }
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
                "error": error_message
            }

    async def _extract_text(self, file_path: str) -> str:
        """
        Extract text from document using Docling OCR

        Args:
            file_path: Path to document file

        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        # Use Docling for comprehensive document conversion
        if DOCLING_AVAILABLE and self.converter:
            try:
                result = self.converter.convert(file_path)

                # Extract text content from conversion result
                text_parts = []

                # Docling provides structured document content
                # Extract text from document structure
                if hasattr(result, 'document'):
                    doc = result.document

                    # Get markdown representation (preserves structure)
                    if hasattr(doc, 'export_to_markdown'):
                        text_parts.append(doc.export_to_markdown())
                    # Fallback: get plain text
                    elif hasattr(doc, 'export_to_text'):
                        text_parts.append(doc.export_to_text())
                    # Last resort: convert to string
                    else:
                        text_parts.append(str(doc))

                text_content = "\n\n".join(text_parts)

                if text_content and len(text_content.strip()) > 0:
                    return text_content
                else:
                    logger.warning("Docling returned empty content, trying fallback extraction")

            except Exception as e:
                logger.error(f"Docling extraction failed: {str(e)}, trying fallback")

        # Fallback extraction methods
        return await self._fallback_extraction(file_path, file_ext)

    async def _extract_text_with_progress(
        self,
        file_path: str,
        document_id: str
    ) -> str:
        """
        Extract text with progress heartbeat updates for long-running OCR

        This wrapper runs the synchronous Docling extraction in a thread pool
        and provides progress updates every 15 seconds to give users feedback
        during long OCR operations (which can take 5-10+ minutes for large PDFs).

        Args:
            file_path: Path to document file
            document_id: Document ID for progress broadcasting

        Returns:
            Extracted text content
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # Create executor for running sync Docling code
        executor = ThreadPoolExecutor(max_workers=1)

        # Start extraction in background thread
        extraction_task = asyncio.get_event_loop().run_in_executor(
            executor,
            self._extract_text_sync,  # Synchronous version
            file_path
        )

        # Provide heartbeat updates while extraction runs
        start_time = time.time()
        last_progress = 0

        while not extraction_task.done():
            await asyncio.sleep(15)  # Update every 15 seconds

            elapsed = time.time() - start_time
            # Estimate progress based on elapsed time
            # Most PDFs take 1-5 minutes, so we estimate up to 25% during extraction phase
            # This is intentionally conservative to avoid showing 100% prematurely
            estimated_progress = min(25, int((elapsed / 180) * 30))  # Max 25% over 3 minutes

            if estimated_progress > last_progress:
                # Update MongoDB
                await self.db.document_metadata.update_one(
                    {"document_id": document_id},
                    {"$set": {"processing_progress": estimated_progress}}
                )

                # Broadcast progress update via SSE
                await self.events_manager.broadcast_progress(
                    document_id=document_id,
                    status="processing",
                    step="extracting_text",
                    progress=estimated_progress
                )

                logger.info(
                    f"OCR extraction heartbeat for {document_id}: "
                    f"{estimated_progress}% ({elapsed:.0f}s elapsed)"
                )

                last_progress = estimated_progress

        # Get result
        return await extraction_task

    def _extract_text_sync(self, file_path: str) -> str:
        """
        Synchronous version of text extraction for thread pool execution

        This is needed because Docling's converter.convert() is synchronous
        and cannot be awaited directly.

        Args:
            file_path: Path to document file

        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        # Use Docling for comprehensive document conversion
        if DOCLING_AVAILABLE and self.converter:
            try:
                # Time the conversion for performance monitoring
                conversion_start = time.time()
                result = self.converter.convert(file_path)
                conversion_time = time.time() - conversion_start

                # Log performance metrics
                logger.info(f"✓ Docling conversion completed in {conversion_time:.2f}s")

                # Log timing details if available
                if hasattr(result, 'timings') and result.timings:
                    pipeline_times = result.timings.get("pipeline_total", {})
                    if hasattr(pipeline_times, 'times'):
                        logger.info(f"  Pipeline timings: {pipeline_times.times}")

                # DEBUG: Log document structure to understand what was processed
                if hasattr(result, 'document'):
                    doc = result.document
                    picture_count = 0
                    try:
                        from docling_core.types.doc import PictureItem
                        for element, level in doc.iterate_items():
                            if isinstance(element, PictureItem):
                                picture_count += 1
                        logger.info(f"  Found {picture_count} picture elements in document")
                    except Exception as e:
                        logger.warning(f"  Could not count pictures: {str(e)}")

                # Extract text content from conversion result
                text_parts = []

                if hasattr(result, 'document'):
                    doc = result.document

                    # Export main document text (markdown format)
                    if hasattr(doc, 'export_to_markdown'):
                        markdown_text = doc.export_to_markdown()
                        text_parts.append(markdown_text)
                    elif hasattr(doc, 'export_to_text'):
                        text_parts.append(doc.export_to_text())
                    else:
                        text_parts.append(str(doc))

                    # CRITICAL FIX: Manually extract picture descriptions from GPT-4 Vision
                    # The export_to_markdown() doesn't include picture descriptions by default
                    picture_descriptions = []
                    try:
                        from docling_core.types.doc import PictureItem

                        # Iterate through all document items to find pictures
                        for element, level in doc.iterate_items():
                            if isinstance(element, PictureItem):
                                logger.info(f"  Processing PictureItem: {element.self_ref if hasattr(element, 'self_ref') else 'unknown'}")

                                # Check if this picture has GPT-4 Vision descriptions
                                if hasattr(element, 'annotations') and element.annotations:
                                    logger.info(f"    Found {len(element.annotations)} annotations")
                                    for idx, annotation in enumerate(element.annotations):
                                        # DEBUG: Log annotation type and attributes
                                        annotation_type = type(annotation).__name__
                                        logger.info(f"    Annotation {idx}: type={annotation_type}, attributes={dir(annotation)}")

                                        # Extract text from picture description annotation
                                        if hasattr(annotation, 'text') and annotation.text:
                                            picture_descriptions.append(
                                                f"\n[IMAGE DESCRIPTION - GPT-4 Vision]:\n{annotation.text}\n"
                                            )
                                            logger.info(f"✓ Extracted GPT-4 Vision description from 'text' attribute ({len(annotation.text)} chars)")
                                        # Alternative: check for 'description' attribute
                                        elif hasattr(annotation, 'description') and annotation.description:
                                            picture_descriptions.append(
                                                f"\n[IMAGE DESCRIPTION - GPT-4 Vision]:\n{annotation.description}\n"
                                            )
                                            logger.info(f"✓ Extracted GPT-4 Vision description from 'description' attribute ({len(annotation.description)} chars)")
                                        else:
                                            # Try to extract any text-like content
                                            logger.warning(f"    Annotation has no 'text' or 'description' attribute. Trying str(annotation)...")
                                            annotation_str = str(annotation)
                                            if annotation_str and len(annotation_str) > 10:
                                                picture_descriptions.append(
                                                    f"\n[IMAGE DESCRIPTION - GPT-4 Vision]:\n{annotation_str}\n"
                                                )
                                                logger.info(f"✓ Extracted GPT-4 Vision description from str() ({len(annotation_str)} chars)")
                                else:
                                    logger.warning(f"    PictureItem has NO annotations - GPT-4 Vision was not invoked!")
                    except Exception as e:
                        logger.warning(f"Failed to extract picture descriptions: {str(e)}")

                    # Append all picture descriptions to the text content
                    if picture_descriptions:
                        text_parts.extend(picture_descriptions)
                        logger.info(f"✓ Added {len(picture_descriptions)} picture descriptions to extracted text")
                    else:
                        logger.warning("⚠ No picture descriptions found - GPT-4 Vision may not have been invoked")

                text_content = "\n\n".join(text_parts)

                if text_content and len(text_content.strip()) > 0:
                    logger.info(f"✓ Extracted {len(text_content)} characters from document")
                    return text_content
                else:
                    logger.warning("Docling returned empty content")

            except Exception as e:
                logger.error(f"Docling extraction failed: {str(e)}")

        # If Docling fails or unavailable, raise error for async fallback
        raise ValueError("Docling extraction failed, fallback needed")

    async def _fallback_extraction(self, file_path: str, file_ext: str) -> str:
        """
        Fallback text extraction for when Docling is unavailable

        Args:
            file_path: Path to document
            file_ext: File extension

        Returns:
            Extracted text
        """
        text_content = ""

        # PDF extraction
        if file_ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_parts = []
                    for page in pdf_reader.pages:
                        text_parts.append(page.extract_text())
                    text_content = "\n\n".join(text_parts)
            except Exception as e:
                logger.error(f"PDF extraction failed: {str(e)}")

        # DOCX extraction
        elif file_ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                text_parts = [paragraph.text for paragraph in doc.paragraphs]
                text_content = "\n\n".join(text_parts)
            except Exception as e:
                logger.error(f"DOCX extraction failed: {str(e)}")

        # PPTX extraction
        elif file_ext in ['.ppt', '.pptx']:
            try:
                from pptx import Presentation
                prs = Presentation(file_path)
                text_parts = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text_parts.append(shape.text)
                text_content = "\n\n".join(text_parts)
            except Exception as e:
                logger.error(f"PPTX extraction failed: {str(e)}")

        # Excel extraction
        elif file_ext in ['.xls', '.xlsx']:
            try:
                from openpyxl import load_workbook
                wb = load_workbook(file_path, read_only=True, data_only=True)
                text_parts = []
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        row_text = " | ".join([str(cell) for cell in row if cell is not None])
                        if row_text.strip():
                            text_parts.append(row_text)
                text_content = "\n".join(text_parts)
            except Exception as e:
                logger.error(f"Excel extraction failed: {str(e)}")

        # Image files - note: basic OCR would require additional libraries
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            logger.warning(f"Image file {file_ext} - OCR not implemented in fallback")
            text_content = f"[Image file: {os.path.basename(file_path)}]"

        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        return text_content

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Chunk text into segments with token-based sizing

        Args:
            text: Text to chunk
            chunk_size: Target size in tokens (default 500)
            overlap: Overlap between chunks in tokens (default 50)

        Returns:
            List of text chunks
        """
        # Split into sentences first to maintain semantic boundaries
        # Simple sentence splitting (can be enhanced with nltk if needed)
        sentences = []
        current_sentence = []

        for char in text:
            current_sentence.append(char)
            if char in '.!?' and len(current_sentence) > 10:
                sentences.append(''.join(current_sentence).strip())
                current_sentence = []

        # Add remaining text
        if current_sentence:
            sentences.append(''.join(current_sentence).strip())

        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))

            # If adding this sentence exceeds chunk size, start new chunk
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Keep overlap sentences for context
                overlap_sentences = []
                overlap_tokens = 0
                for sent in reversed(current_chunk):
                    sent_tokens = len(self.encoding.encode(sent))
                    if overlap_tokens + sent_tokens <= overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = overlap_tokens

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

        # Filter out very small chunks
        chunks = [chunk for chunk in chunks if len(self.encoding.encode(chunk)) > 10]

        return chunks

    async def _generate_embeddings_batch(
        self,
        chunks: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for chunks in batches

        Args:
            chunks: List of text chunks
            batch_size: Batch size for API calls (max 2048 for OpenAI)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            try:
                embeddings = await self.openai_service.generate_embeddings_batch(batch)
                all_embeddings.extend(embeddings)

                logger.debug(f"Generated embeddings for batch {i//batch_size + 1}")

            except Exception as e:
                logger.error(f"Batch embedding generation failed: {str(e)}")
                raise

        return all_embeddings

    async def _store_vectors(
        self,
        document_id: str,
        filename: str,
        category: str,
        uploader_name: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """
        Store vectors in Pinecone with metadata

        Args:
            document_id: Document ID
            filename: Original filename
            category: Document category
            uploader_name: Uploader username
            chunks: Text chunks
            embeddings: Embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk count ({len(chunks)}) doesn't match embedding count ({len(embeddings)})"
            )

        # Prepare vectors for Pinecone
        vectors = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{document_id}_chunk{idx}"

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "category": category,
                    "uploader_name": uploader_name,
                    "chunk_index": idx,
                    "text_content": chunk[:1000]  # Limit metadata size
                }
            })

        # Upsert to Pinecone in batches (Pinecone recommends 100 vectors per batch)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]

            try:
                await self.pinecone_service.upsert_vectors(batch)
                logger.debug(f"Upserted batch {i//batch_size + 1} to Pinecone")

            except Exception as e:
                logger.error(f"Pinecone upsert failed: {str(e)}")
                raise


# Singleton instance
_document_processor = None


def get_document_processor() -> DocumentProcessor:
    """Get singleton document processor instance"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor
