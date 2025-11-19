"""
JSON Property Processor with AI-Powered Property Extraction

Processes JSON files containing machinery/equipment data with automatic
property detection using OpenAI's GPT models. Supports both structured
E-code format and unstructured JSON data.

Features:
- AI-powered property extraction from unstructured JSON
- Automatic property type detection
- Text chunking for large descriptions
- Embedding generation for semantic search
- Weaviate Machinery collection integration
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from app.services.openai_service import get_openai_service
from app.services.weaviate_service import weaviate_service
from app.services.text_chunker import get_text_chunker
from app.utils.property_extractor import PropertyExtractor, DeviceInfo
from app.core.database import get_database
from app.services.document_events import get_document_events_manager

logger = logging.getLogger(__name__)


class JsonPropertyProcessor:
    """
    Process JSON files with AI-powered property extraction

    Supports two modes:
    1. Structured E-code format (existing machinery data)
    2. Unstructured JSON with AI extraction (new feature)
    """

    def __init__(self):
        self.openai_service = get_openai_service()
        self.weaviate_service = weaviate_service
        self.text_chunker = get_text_chunker()
        self.property_extractor = PropertyExtractor()
        self.events_manager = get_document_events_manager()

    async def process_json_file(
        self,
        file_path: str,
        document_id: str,
        filename: str,
        category: str,
        uploader_id: str,
        uploader_name: str
    ) -> Dict[str, Any]:
        """
        Process JSON file with AI property extraction

        Args:
            file_path: Path to JSON file
            document_id: Unique document ID
            filename: Original filename
            category: Document category
            uploader_id: Uploader user ID
            uploader_name: Uploader username (tenant)

        Returns:
            Processing result with stats
        """
        try:
            logger.info(f"[JSON] Starting processing for {filename} (ID: {document_id})")

            # Update status: parsing JSON
            await self._update_status(
                document_id, "processing", "parsing_json", 10
            )

            # Parse JSON file
            json_data = await self._parse_json_file(file_path)

            # Detect JSON structure and extract properties
            await self._update_status(
                document_id, "processing", "extracting_properties", 20
            )

            properties_data = await self._extract_properties_with_ai(json_data, filename)

            # Generate embeddings
            await self._update_status(
                document_id, "processing", "generating_embeddings", 50
            )

            objects_with_embeddings = await self._generate_embeddings(
                properties_data, document_id, filename, category,
                uploader_id, uploader_name
            )

            # Upload to Weaviate
            await self._update_status(
                document_id, "processing", "uploading_to_weaviate", 70
            )

            result = await self._upload_to_weaviate(
                objects_with_embeddings, uploader_name
            )

            # Update final status
            await self._update_status(
                document_id, "completed", "completed", 100,
                chunk_count=result['success']
            )

            logger.info(
                f"[JSON] Successfully processed {filename}: "
                f"{result['success']} properties uploaded"
            )

            return {
                "status": "completed",
                "properties_extracted": len(properties_data),
                "properties_uploaded": result['success'],
                "failed": result['failed']
            }

        except Exception as e:
            error_msg = f"JSON processing failed: {str(e)}"
            logger.error(f"[JSON] {error_msg}", exc_info=True)

            await self._update_status(
                document_id, "failed", "failed", 0,
                error_message=error_msg
            )

            raise

    async def _parse_json_file(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON file with UTF-8 encoding"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to read JSON file: {str(e)}")

    async def _extract_properties_with_ai(
        self,
        json_data: Dict[str, Any],
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Extract properties from JSON using AI

        Detects if JSON is in structured E-code format or needs AI extraction
        """
        # Check if this is structured E-code format
        if self._is_ecode_format(json_data):
            logger.info(f"[JSON] Detected E-code format in {filename}")
            return await self._extract_ecode_properties(json_data)
        else:
            logger.info(f"[JSON] Using AI property extraction for {filename}")
            return await self._extract_unstructured_properties(json_data)

    def _is_ecode_format(self, data: Dict[str, Any]) -> bool:
        """Check if JSON follows E-code machinery format"""
        # Check for common E-code structure indicators
        if isinstance(data, dict):
            # Check if it has a "devices" dictionary (common format)
            if 'devices' in data and isinstance(data['devices'], dict):
                # Check first device in the devices dict
                first_device = next(iter(data['devices'].values()), None)
                if first_device and isinstance(first_device, dict):
                    if 'device_info' in first_device or 'properties' in first_device:
                        return True
            # Check if it has device_info and properties keys directly
            if 'device_info' in data or 'properties' in data:
                return True
            # Check if keys contain E-codes
            for key in data.keys():
                if isinstance(key, str) and key.startswith('E') and key[1:5].isdigit():
                    return True
        elif isinstance(data, list):
            # Check if it's a list of machines with E-codes
            if data and isinstance(data[0], dict):
                first_item = data[0]
                if 'device_info' in first_item or any(
                    k.startswith('E') for k in first_item.keys() if isinstance(k, str)
                ):
                    return True
        return False

    async def _extract_ecode_properties(
        self,
        json_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract properties from E-code format JSON"""
        properties = []

        # Handle nested "devices" dictionary (common format)
        if 'devices' in json_data and isinstance(json_data['devices'], dict):
            machines = list(json_data['devices'].values())
        # Handle list of machines
        elif isinstance(json_data, list):
            machines = json_data
        # Handle single machine
        else:
            machines = [json_data]

        for machine in machines:
            # Extract device info
            device_info = machine.get('device_info', {})
            name = device_info.get('name', 'Unknown')
            serial_number = device_info.get('serial_number', '')
            inventory_number = device_info.get('inventory_number', '')

            # Extract E-code properties
            machine_props = machine.get('properties', {})

            property_dict = {}
            description_parts = []

            for ecode_key, value_data in machine_props.items():
                parsed = self.property_extractor.parse_ecode_key(ecode_key)
                if parsed:
                    ecode = parsed['code']
                    desc = parsed['description']
                    unit = parsed['unit']

                    # Extract actual value from nested structure
                    if isinstance(value_data, dict) and 'value' in value_data:
                        value = value_data['value']
                        # Use unit from data if available, otherwise from E-code
                        if 'unit' in value_data and value_data['unit']:
                            unit = value_data['unit']
                    else:
                        value = value_data

                    # Store property
                    property_dict[ecode] = value

                    # Build description
                    if unit:
                        description_parts.append(f"{desc}: {value} {unit}")
                    else:
                        description_parts.append(f"{desc}: {value}")

            # Build full description with name, serial, and inventory for better searchability
            full_description = f"Machine: {name}"
            if serial_number:
                full_description += f" | Serial Number: {serial_number}"
            if inventory_number:
                full_description += f" | Inventory Number: {inventory_number}"
            if description_parts:
                full_description += " | " + ' | '.join(description_parts)

            properties.append({
                'name': name,
                'serial_number': serial_number,
                'inventory_number': inventory_number,
                'properties': property_dict,
                'description': full_description,
                'manufacturer': self._extract_manufacturer(name),
                'model': self._extract_model(name)
            })

        return properties

    async def _extract_unstructured_properties(
        self,
        json_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract properties from unstructured JSON using AI

        Uses OpenAI to automatically detect and structure properties
        """
        # Convert JSON to text for AI processing
        json_text = json.dumps(json_data, indent=2, ensure_ascii=False)

        # Truncate if too large (keep first 10000 chars)
        if len(json_text) > 10000:
            json_text = json_text[:10000] + "\n... [truncated]"

        prompt = f"""Analyze the following JSON data containing machinery or equipment information.
Extract structured properties from this data.

For each machine/equipment found, extract:
1. name: The equipment/machine name
2. serial_number: Serial number if available (or generate from available IDs)
3. manufacturer: Manufacturer name
4. model: Model designation
5. properties: Key-value pairs of specifications (power, weight, dimensions, etc.)
6. description: Human-readable summary

JSON Data:
{json_text}

Return a JSON array of machines with this structure:
[
  {{
    "name": "Machine Name",
    "serial_number": "SN123",
    "manufacturer": "Manufacturer",
    "model": "Model",
    "properties": {{"property_name": "value"}},
    "description": "Summary of key specifications"
  }}
]

If the JSON is not about machinery/equipment, extract whatever entities make sense and structure them similarly.
"""

        try:
            # Call OpenAI for extraction
            response = await self.openai_service.generate_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant specialized in machinery and equipment specifications. Extract structured data from unstructured JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )

            # Log response for debugging
            logger.info(f"[JSON] OpenAI response keys: {list(response.keys())}")

            # Check if response has content (openai_service returns simplified format)
            if 'content' not in response:
                logger.error(f"[JSON] OpenAI response missing 'content': {response}")
                raise ValueError(f"Invalid OpenAI response: {response.get('error', 'Unknown error')}")

            # Parse AI response (content is already extracted by openai_service)
            ai_response = response['content'].strip()

            # Extract JSON from markdown code blocks if present
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0].strip()

            extracted_data = json.loads(ai_response)

            # Ensure it's a list
            if isinstance(extracted_data, dict):
                extracted_data = [extracted_data]

            logger.info(f"[JSON] AI extracted {len(extracted_data)} entities")

            return extracted_data

        except json.JSONDecodeError as e:
            logger.error(f"[JSON] Failed to parse AI response: {e}")
            # Fallback: create a simple property from the JSON
            return [{
                'name': 'Imported Data',
                'serial_number': str(uuid.uuid4())[:8],
                'manufacturer': 'Unknown',
                'model': 'Unknown',
                'properties': {},
                'description': json.dumps(json_data, ensure_ascii=False)[:500]
            }]

    async def _generate_embeddings(
        self,
        properties_data: List[Dict[str, Any]],
        document_id: str,
        filename: str,
        category: str,
        uploader_id: str,
        uploader_name: str
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for machinery descriptions"""
        texts = [item['description'] for item in properties_data]

        # Generate embeddings in batch
        embeddings = await self.openai_service.generate_embeddings_batch(texts)

        # Combine with data
        objects = []
        for i, (item, embedding) in enumerate(zip(properties_data, embeddings)):
            obj = {
                'id': str(uuid.uuid4()),
                'vector': embedding,
                'properties': {
                    'name': item['name'],
                    'serial_number': item['serial_number'],
                    'manufacturer': item.get('manufacturer', 'Unknown'),
                    'model': item.get('model', 'Unknown'),
                    'inventory_number': item.get('inventory_number', ''),
                    'text_content': item['description'],  # Add description for BM25 search and AI context
                    'created_at': datetime.utcnow().isoformat() + 'Z',
                    **self._flatten_properties(item.get('properties', {}))
                }
            }
            objects.append(obj)

        return objects

    def _flatten_properties(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten properties to Weaviate schema with GraphQL-compliant names"""
        import re
        flattened = {}
        for key, value in props.items():
            # Convert to Weaviate-compatible property name (GraphQL naming rules)
            # Remove invalid characters and replace spaces with underscores
            sanitized_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
            # Ensure it starts with a letter or underscore
            if sanitized_key and not re.match(r'^[_A-Za-z]', sanitized_key):
                sanitized_key = '_' + sanitized_key
            # Truncate to 230 chars (GraphQL limit)
            sanitized_key = sanitized_key[:230]

            prop_key = sanitized_key if key.startswith('E') else f"property_{sanitized_key}"
            flattened[prop_key] = str(value)
        return flattened

    async def _upload_to_weaviate(
        self,
        objects: List[Dict[str, Any]],
        tenant: str
    ) -> Dict[str, int]:
        """Upload objects to Weaviate Machinery collection (shared, no tenant isolation)"""
        # Use smaller batch size to avoid gRPC message size limit (10MB)
        # With embeddings (3072 dims), each object is ~12-15KB
        # Batch size of 100 = ~1.5MB per batch (well under 10MB limit)
        result = await self.weaviate_service.batch_upsert(
            objects=objects,
            collection_name='Machinery',
            tenant=None,  # No tenant - data is shared globally
            batch_size=100  # Smaller batches to avoid gRPC size limit
        )
        return result

    async def _update_status(
        self,
        document_id: str,
        status: str,
        step: str,
        progress: int,
        chunk_count: int = 0,
        error_message: Optional[str] = None
    ):
        """Update processing status in MongoDB and broadcast via SSE"""
        db = get_database()

        update_data = {
            'processing_status': status,
            'processing_step': step,
            'processing_progress': progress
        }

        if chunk_count > 0:
            update_data['chunk_count'] = chunk_count

        if error_message:
            update_data['error_message'] = error_message

        await db.document_metadata.update_one(
            {'document_id': document_id},
            {'$set': update_data}
        )

        # Broadcast update via SSE
        await self.events_manager.broadcast_progress(
            document_id=document_id,
            status=status,
            step=step,
            progress=progress,
            chunk_count=chunk_count if chunk_count > 0 else None,
            error=error_message
        )

    def _extract_manufacturer(self, name: str) -> str:
        """Extract manufacturer from machine name"""
        # Simple extraction: first word
        parts = name.split()
        return parts[0] if parts else 'Unknown'

    def _extract_model(self, name: str) -> str:
        """Extract model from machine name"""
        # Simple extraction: everything after first word
        parts = name.split(maxsplit=1)
        return parts[1] if len(parts) > 1 else 'Unknown'


def get_json_property_processor() -> JsonPropertyProcessor:
    """Get singleton instance of JSON processor"""
    return JsonPropertyProcessor()
