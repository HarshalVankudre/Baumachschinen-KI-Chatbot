"""
Machinery Data Processing Service

Handles JSON machinery data processing for the vector search system:
- Parse and validate JSON machinery data
- Generate embeddings for machinery descriptions
- Prepare vectors for Pinecone machinery namespace
"""

import logging
import json
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, UTC

from app.services.openai_service import get_openai_service
from app.services.pinecone_service import get_pinecone_service
from app.constants import NAMESPACE_MACHINERY

logger = logging.getLogger(__name__)


class MachineryDataService:
    """
    Service for processing machinery JSON data into hybrid RAG system

    Workflow:
    1. Validate JSON structure
    2. Generate rich text descriptions for embeddings
    3. Create embeddings using OpenAI
    4. Upsert vectors to Pinecone machinery namespace
    """

    def __init__(self):
        """Initialize service dependencies"""
        self.openai_service = get_openai_service()
        self.pinecone_service = get_pinecone_service()
        self.property_line_pattern = re.compile(
            r"^\*\s*(E\d+)\s*-\s*([^:]+):\s*(.+)$"
        )

    async def process_machinery_json(
        self,
        file_path: str,
        uploader_name: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process machinery JSON file end-to-end with transaction rollback

        Args:
            file_path: Path to JSON file
            uploader_name: Username of uploader
            document_id: Optional document ID for tracking

        Returns:
            Processing result with statistics

        Raises:
            ValueError: If JSON validation fails
            Exception: If processing fails
        """
        logger.info(f"Processing machinery JSON: {file_path}")
        vectors_created = False
        vector_ids = []

        try:
            # Step 1: Load and validate JSON
            machines = await self._load_and_validate_json(file_path)
            logger.info(f"Loaded {len(machines)} machines from JSON")

            # Step 2: Generate embeddings for machinery descriptions
            vectors, machine_data_list = await self._prepare_machinery_vectors(
                machines,
                uploader_name,
                document_id
            )
            logger.info(f"Generated {len(vectors)} embeddings for machinery")
            vector_ids = [v["id"] for v in vectors]

            # Step 3: Upsert to Pinecone machinery namespace
            await self.pinecone_service.upsert_vectors(
                vectors=vectors,
                namespace=NAMESPACE_MACHINERY
            )
            vectors_created = True
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone machinery namespace")

            return {
                "status": "success",
                "machines_processed": len(machines),
                "vectors_created": len(vectors),
                "pinecone_namespace": NAMESPACE_MACHINERY,
            }

        except Exception as e:
            # Rollback Pinecone on error
            if vectors_created and vector_ids:
                logger.error(f"Processing failed, rolling back {len(vector_ids)} Pinecone vectors")
                try:
                    await self.pinecone_service.delete_vectors(
                        ids=vector_ids,
                        namespace=NAMESPACE_MACHINERY
                    )
                    logger.info("Pinecone rollback successful")
                except Exception as rollback_error:
                    logger.critical(f"ROLLBACK FAILED - Manual cleanup needed: {rollback_error}")
                    logger.critical(f"Orphaned vector IDs: {vector_ids}")

            logger.error(f"Machinery data processing failed: {str(e)}", exc_info=True)
            raise

    async def _load_and_validate_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load and validate machinery JSON file

        Expected structure:
        {
          "machines": [
            {
              "id": "unique-id",
              "model": "Excavator X500",
              "manufacturer": "BrandName",
              "category": "Excavator",
              "specifications": {...},
              "features": [...],
              "description": "text for embedding"
            }
          ]
        }

        Args:
            file_path: Path to JSON file

        Returns:
            List of validated machine dictionaries

        Raises:
            ValueError: If JSON is invalid or required fields missing
        """
        try:
            if file_path.endswith(".jsonl"):
                machines = self._load_jsonl_file(file_path)
            else:
                machines = self._load_json_array(file_path)

            logger.info(f"Validated {len(machines)} machines")
            return machines

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            raise ValueError(f"JSON validation failed: {str(e)}")

    def _load_json_array(self, file_path: str) -> List[Dict[str, Any]]:
        """Load machines from traditional JSON structure."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "machines" in data:
            machines = data["machines"]
        elif isinstance(data, list):
            machines = data
        else:
            raise ValueError("JSON must contain 'machines' array or be an array of machines")

        validated = []
        for idx, machine in enumerate(machines):
            machine_id = (
                machine.get("id")
                or machine.get("serial_number")
                or machine.get("inventory_number")
            )
            if not machine_id:
                logger.warning(f"Machine at index {idx} missing ID, generating one")
                machine["id"] = f"machine_{uuid.uuid4().hex[:8]}"
            else:
                machine["id"] = str(machine_id)

            if not machine.get("model") and not machine.get("name"):
                machine["model"] = f"Machine {machine['id']}"

            validated.append(machine)

        return validated

    def _load_jsonl_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load machines from JSON Lines file."""
        machines: List[Dict[str, Any]] = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSONL entry at line {line_number}: {e}"
                    )

                machine = self._convert_jsonl_record(record, line_number)
                machines.append(machine)

        return machines

    def _convert_jsonl_record(
        self,
        record: Dict[str, Any],
        line_number: int
    ) -> Dict[str, Any]:
        """Convert JSONL record with content.text into internal machine format."""
        machine_id = str(record.get("id") or f"machine_{uuid.uuid4().hex[:8]}")
        content = record.get("content", {})
        text_block = content.get("text") or ""

        if not text_block:
            raise ValueError(f"JSONL entry at line {line_number} missing content.text")

        device_info = self._parse_device_info(text_block)
        specs, manufacturer = self._parse_properties(text_block)

        name = device_info.get("name") or machine_id
        serial_number = device_info.get("serial_number")
        inventory_number = device_info.get("inventory_number")

        machine = {
            "id": machine_id,
            "name": name,
            "model": name,
            "serial_number": serial_number,
            "inventory_number": inventory_number,
            "manufacturer": manufacturer or device_info.get("manufacturer"),
            "category": record.get("category", "Maschine"),
            "specifications": specs,
            "description": text_block,
            "features": [],
        }

        return machine

    def _parse_device_info(self, text_block: str) -> Dict[str, str]:
        """Extract basic device info from text block."""
        info: Dict[str, str] = {}

        for line in text_block.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.lower().startswith("device name:"):
                info["name"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("serial number:"):
                info["serial_number"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("inventory number:"):
                info["inventory_number"] = line.split(":", 1)[1].strip()

        return info

    def _parse_properties(
        self,
        text_block: str
    ) -> Tuple[Dict[str, str], Optional[str]]:
        """Parse property lines into specifications dict and detect manufacturer."""
        specs: Dict[str, str] = {}
        manufacturer: Optional[str] = None

        for line in text_block.splitlines():
            line = line.strip()
            if not line.startswith("*"):
                continue

            match = self.property_line_pattern.match(line)
            if not match:
                continue

            ecode = match.group(1)
            label = match.group(2).strip()
            raw_value = match.group(3).strip()

            value = raw_value
            unit = ""
            if " - " in raw_value:
                value_part, unit_part = raw_value.split(" - ", 1)
                value = value_part.strip()
                unit = unit_part.strip()

            if unit:
                formatted_value = f"{value} ({unit})"
            else:
                formatted_value = value

            specs[f"{ecode} - {label}"] = formatted_value

            if ecode == "E2170" and not manufacturer:
                manufacturer = value

        return specs, manufacturer

    async def _prepare_machinery_vectors(
        self,
        machines: List[Dict[str, Any]],
        uploader_name: str,
        document_id: Optional[str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Prepare vectors for Pinecone upsert with batch size chunking

        Args:
            machines: List of machine dictionaries
            uploader_name: Uploader username
            document_id: Optional document ID

        Returns:
            Tuple of (vectors, machine_data_list)
        """
        # OpenAI supports up to 2048 inputs per batch, use conservative limit
        BATCH_SIZE = 100

        vectors = []
        machine_data_list = []

        # Process in batches to avoid API limits
        for batch_start in range(0, len(machines), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(machines))
            batch = machines[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start//BATCH_SIZE + 1}: machines {batch_start+1}-{batch_end}")

            # Generate descriptions for this batch
            descriptions = []
            for machine in batch:
                description = self._generate_machine_description(machine)
                descriptions.append(description)

            # Batch generate embeddings
            try:
                embeddings = await self.openai_service.generate_embeddings_batch(descriptions)
            except Exception as e:
                logger.error(f"Batch embedding failed, falling back to one-by-one: {e}")
                # Fallback: generate embeddings one by one
                embeddings = []
                for desc in descriptions:
                    try:
                        emb = await self.openai_service.generate_embedding(desc)
                        embeddings.append(emb)
                    except Exception as single_error:
                        logger.error(f"Single embedding failed: {single_error}")
                        # Skip this machine
                        embeddings.append(None)

            # Prepare vectors for this batch
            for machine, embedding, description in zip(batch, embeddings, descriptions):
                if embedding is None:
                    logger.warning(f"Skipping machine {machine.get('id')} due to embedding failure")
                    continue

                machine_id = machine["id"]
                vector_id = f"machinery_{machine_id}"

                # Extract metadata
                metadata = {
                    "machine_id": machine_id,
                    "model": machine.get("model") or machine.get("name", "Unknown"),
                    "manufacturer": machine.get("manufacturer", "Unknown"),
                    "category": machine.get("category", "Unknown"),
                    "description": description[:1000],  # Truncate for Pinecone metadata limit
                    "uploader_name": uploader_name,
                    "source": "machinery_json",
                    "namespace": NAMESPACE_MACHINERY
                }

                if document_id:
                    metadata["document_id"] = document_id

                # Add specifications to metadata (selected important ones)
                specs = machine.get("specifications", {})
                if specs:
                    # Add key specs to metadata
                    for key in ["weight", "power", "dimensions", "capacity"]:
                        if key in specs:
                            metadata[f"spec_{key}"] = str(specs[key])

                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })

                machine_data_list.append({
                    **machine,
                    "vector_id": vector_id,
                    "description": description
                })

        logger.info(f"Prepared {len(vectors)} vectors from {len(machines)} machines")
        return vectors, machine_data_list

    def _generate_machine_description(self, machine: Dict[str, Any]) -> str:
        """
        Generate rich text description for embedding

        Args:
            machine: Machine dictionary

        Returns:
            Rich text description optimized for semantic search
        """
        parts = []

        # Basic info
        model = machine.get("model") or machine.get("name", "Unknown Machine")
        manufacturer = machine.get("manufacturer", "")
        category = machine.get("category", "")

        if manufacturer:
            parts.append(f"{manufacturer} {model}")
        else:
            parts.append(model)

        if category:
            parts.append(f"Kategorie: {category}")

        # Description
        if "description" in machine and machine["description"]:
            parts.append(machine["description"])

        # Specifications
        specs = machine.get("specifications", {})
        if specs:
            spec_parts = []
            for key, value in specs.items():
                if value:
                    spec_parts.append(f"{key}: {value}")
            if spec_parts:
                parts.append("Spezifikationen: " + ", ".join(spec_parts))

        # Features
        features = machine.get("features", [])
        if features:
            parts.append("Ausstattung: " + ", ".join(str(f) for f in features))

        # Applications/Tasks
        applications = machine.get("applications", [])
        if applications:
            parts.append("Anwendungen: " + ", ".join(str(a) for a in applications))

        description = ". ".join(parts)
        return description



# Singleton
_machinery_data_service = None


def get_machinery_data_service() -> MachineryDataService:
    """Get singleton machinery data service"""
    global _machinery_data_service
    if _machinery_data_service is None:
        _machinery_data_service = MachineryDataService()
    return _machinery_data_service
