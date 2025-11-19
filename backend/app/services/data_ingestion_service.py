"""
Machinery Data Ingestion Service

Processes JSON machinery data and uploads to Pinecone for semantic search.

Pipeline:
1. Parse JSON file with machinery specifications
2. Validate data structure and E-code properties
3. Generate rich embeddings for semantic search
4. Upload vectors to Pinecone "machinery" namespace

Features:
- Handles all 406 E-code properties
- UTF-8 encoding normalization for German umlauts
- Batch processing for efficiency
- Idempotent operations (safe to re-run)
- Comprehensive error handling and logging
- Progress tracking and statistics
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import asyncio

from app.services.openai_service import get_openai_service
from app.services.weaviate_service import weaviate_service
from app.utils.umlaut_normalizer import normalize_umlauts, normalize_dict, UmlautNormalizer

logger = logging.getLogger(__name__)


@dataclass
class MachineData:
    """
    Parsed machine data with metadata

    Attributes:
        machine_id: Unique identifier (name_serial)
        name: Machine name
        serial_number: Serial number
        inventory_number: Inventory number
        manufacturer: Extracted manufacturer name
        model: Extracted model name
        properties: Dictionary of E-code properties {E-code: value}
        raw_data: Original parsed data
    """
    machine_id: str
    name: str
    serial_number: str
    inventory_number: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionStats:
    """
    Statistics for ingestion process

    Tracks progress, successes, failures, and resource usage
    """
    total_machines: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    unique_ecodes: Set[str] = field(default_factory=set)
    embedding_tokens: int = 0
    vectors_uploaded: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "total_machines": self.total_machines,
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "unique_ecodes": len(self.unique_ecodes),
            "embedding_tokens": self.embedding_tokens,
            "vectors_uploaded": self.vectors_uploaded,
            "error_count": len(self.errors)
        }


class DataIngestionService:
    """
    Service for ingesting machinery data into Pinecone

    Handles end-to-end pipeline from JSON file to Pinecone vectors
    """

    # E-code pattern: Exxxx - Description [unit]
    ECODE_PATTERN = re.compile(r'^(E\d+)\s*-\s*(.+?)(?:\s*\[(.+?)\])?$')

    def __init__(self):
        """Initialize ingestion service with required dependencies"""
        self.openai_service = get_openai_service()
        self.weaviate_service = weaviate_service
        self.stats = IngestionStats()

    def parse_json_file(self, file_path: str) -> Dict[str, Dict]:
        """
        Parse JSON file with UTF-8 encoding normalization

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary of machine data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        logger.info(f"Reading JSON file: {file_path}")

        # Read with explicit UTF-8 encoding
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Normalize umlauts in the entire structure
        logger.info("Normalizing UTF-8 encoding for German umlauts...")
        normalized_data = normalize_dict(raw_data, recursive=True)

        logger.info(f"Loaded {len(normalized_data)} machines from JSON")
        return normalized_data

    def validate_machine_data(self, machine_id: str, machine_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate machine data structure

        Args:
            machine_id: Machine identifier
            machine_data: Raw machine data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required top-level keys
        if "device_info" not in machine_data:
            return False, "Missing 'device_info' key"

        if "properties" not in machine_data:
            return False, "Missing 'properties' key"

        device_info = machine_data["device_info"]

        # Check required device_info fields
        required_fields = ["name", "serial_number"]
        for field in required_fields:
            if field not in device_info or not device_info[field]:
                return False, f"Missing or empty required field: device_info.{field}"

        # Validate properties structure
        properties = machine_data["properties"]
        if not isinstance(properties, dict):
            return False, "'properties' must be a dictionary"

        # Check that at least some properties exist
        if len(properties) == 0:
            return False, "No properties defined"

        return True, None

    def extract_ecode_from_property(self, property_name: str) -> Optional[str]:
        """
        Extract E-code from property name

        Args:
            property_name: Property name like "E1730 - Gewicht [kg]"

        Returns:
            E-code like "E1730" or None if not found

        Example:
            >>> extract_ecode_from_property("E1730 - Gewicht [kg]")
            "E1730"
        """
        match = self.ECODE_PATTERN.match(property_name)
        if match:
            return match.group(1)  # Return E-code (e.g., "E1730")
        return None

    def extract_manufacturer_model(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract manufacturer and model from machine name

        Args:
            name: Machine name like "Caterpillar 320D" or "Liebherr R944C"

        Returns:
            Tuple of (manufacturer, model)

        Example:
            >>> extract_manufacturer_model("Caterpillar 320D Excavator")
            ("Caterpillar", "320D")
        """
        # Common manufacturers
        manufacturers = [
            "Caterpillar", "CAT", "Komatsu", "Liebherr", "Hitachi", "Volvo",
            "John Deere", "JCB", "Bobcat", "Case", "Doosan", "Hyundai",
            "Kobelco", "Kubota", "Manitou", "New Holland", "Takeuchi",
            "Terex", "Wirtgen", "Bomag", "Hamm", "Dynapac", "Ammann"
        ]

        name_parts = name.split()

        # Try to find manufacturer in name
        manufacturer = None
        for mfg in manufacturers:
            if mfg.lower() in name.lower():
                manufacturer = mfg
                break

        # Extract model (usually alphanumeric after manufacturer)
        model = None
        if manufacturer and len(name_parts) > 1:
            # Find manufacturer position
            for i, part in enumerate(name_parts):
                if part.lower() == manufacturer.lower():
                    # Model is typically the next part
                    if i + 1 < len(name_parts):
                        model = name_parts[i + 1]
                    break

        return manufacturer, model

    def parse_machine(self, machine_id: str, machine_data: Dict) -> Optional[MachineData]:
        """
        Parse and structure machine data

        Args:
            machine_id: Machine identifier
            machine_data: Raw machine data from JSON

        Returns:
            MachineData object or None if parsing fails
        """
        try:
            # Validate data
            is_valid, error = self.validate_machine_data(machine_id, machine_data)
            if not is_valid:
                logger.error(f"Invalid data for {machine_id}: {error}")
                self.stats.errors.append({
                    "machine_id": machine_id,
                    "error": error,
                    "type": "validation"
                })
                return None

            device_info = machine_data["device_info"]
            properties_raw = machine_data["properties"]

            # Extract basic info
            name = device_info["name"]
            serial_number = device_info.get("serial_number", "")
            inventory_number = device_info.get("inventory_number", "")

            # Extract manufacturer and model
            manufacturer, model = self.extract_manufacturer_model(name)

            # Parse properties and extract E-codes
            properties = {}
            for prop_name, prop_data in properties_raw.items():
                ecode = self.extract_ecode_from_property(prop_name)
                if ecode:
                    # Track unique E-codes
                    self.stats.unique_ecodes.add(ecode)

                    # Extract value
                    if isinstance(prop_data, dict):
                        value = prop_data.get("value", "")
                    else:
                        value = str(prop_data)

                    properties[ecode] = {
                        "value": value,
                        "full_name": prop_name,
                        "raw": prop_data
                    }

            # Create MachineData object
            machine = MachineData(
                machine_id=machine_id,
                name=name,
                serial_number=serial_number,
                inventory_number=inventory_number,
                manufacturer=manufacturer,
                model=model,
                properties=properties,
                raw_data=machine_data
            )

            return machine

        except Exception as e:
            logger.error(f"Error parsing machine {machine_id}: {e}", exc_info=True)
            self.stats.errors.append({
                "machine_id": machine_id,
                "error": str(e),
                "type": "parsing"
            })
            return None

    def create_embedding_text(self, machine: MachineData) -> str:
        """
        Create rich text description for embedding

        Args:
            machine: Parsed machine data

        Returns:
            Rich text description optimized for semantic search

        Example output:
            Machine: Caterpillar 320D Excavator
            Manufacturer: Caterpillar
            Model: 320D
            Serial: ABC123
            Inventory: INV456

            Specifications:
            - Gewicht: 1200 kg
            - Motor Leistung: 168 kW
            - Klimaanlage: Ja
            ...
        """
        lines = []

        # Header with machine info
        lines.append(f"Machine: {machine.name}")

        if machine.manufacturer:
            lines.append(f"Manufacturer: {machine.manufacturer}")

        if machine.model:
            lines.append(f"Model: {machine.model}")

        if machine.serial_number:
            lines.append(f"Serial Number: {machine.serial_number}")

        if machine.inventory_number:
            lines.append(f"Inventory Number: {machine.inventory_number}")

        lines.append("")  # Empty line
        lines.append("Specifications:")

        # Add properties in a readable format
        for ecode, prop_data in sorted(machine.properties.items()):
            prop_name = prop_data["full_name"]
            value = prop_data["value"]

            # Extract just the description (remove E-code prefix)
            match = self.ECODE_PATTERN.match(prop_name)
            if match:
                description = match.group(2)  # Description part
                unit = match.group(3) if match.group(3) else ""
            else:
                description = prop_name
                unit = ""

            # Format: - Description: value unit
            if value:
                if unit:
                    lines.append(f"- {description}: {value}")
                else:
                    lines.append(f"- {description}: {value}")

        return "\n".join(lines)

    async def generate_embeddings_batch(self, machines: List[MachineData]) -> List[Tuple[MachineData, List[float]]]:
        """
        Generate embeddings for a batch of machines

        Args:
            machines: List of MachineData objects

        Returns:
            List of (machine, embedding) tuples
        """
        if not machines:
            return []

        try:
            # Create embedding texts
            texts = [self.create_embedding_text(machine) for machine in machines]

            # Log token usage for first text (sample)
            if texts:
                sample_tokens = self.openai_service.count_tokens(texts[0])
                logger.debug(f"Sample embedding text: {sample_tokens} tokens")

            # Generate embeddings in batch
            embeddings = await self.openai_service.generate_embeddings_batch(texts)

            # Count total tokens (approximate)
            total_tokens = sum(self.openai_service.count_tokens(text) for text in texts)
            self.stats.embedding_tokens += total_tokens

            logger.info(f"Generated {len(embeddings)} embeddings ({total_tokens} tokens)")

            return list(zip(machines, embeddings))

        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}", exc_info=True)
            # Add all machines to errors
            for machine in machines:
                self.stats.errors.append({
                    "machine_id": machine.machine_id,
                    "error": str(e),
                    "type": "embedding"
                })
            return []

    def create_weaviate_object(self, machine: MachineData, embedding: List[float]) -> Dict[str, Any]:
        """
        Create Weaviate object with properties

        Args:
            machine: Machine data
            embedding: Embedding vector

        Returns:
            Weaviate object dictionary
        """
        from datetime import datetime
        import uuid

        # Create properties with all machine data
        properties = {
            "name": machine.name,
            "serial_number": machine.serial_number,
            "inventory_number": machine.inventory_number,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        # Add manufacturer and model if available
        if machine.manufacturer:
            properties["manufacturer"] = machine.manufacturer
        else:
            properties["manufacturer"] = "Unknown"

        if machine.model:
            properties["model"] = machine.model
        else:
            properties["model"] = "Unknown"

        # Add all E-code properties to properties (flatten)
        # Note: Only adding common E-codes defined in schema
        # For production, you'd add all 406 E-code properties to the schema
        for ecode, prop_data in machine.properties.items():
            value = prop_data["value"]
            # Weaviate supports various data types
            if value and ecode in ["E1730", "E2180", "E1930", "E2170", "E2190"]:
                properties[ecode] = str(value)

        # Create deterministic UUID based on serial number
        object_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"machine_{machine.serial_number}"))

        return {
            "id": object_uuid,
            "vector": embedding,  # Pre-computed embedding
            "properties": properties
        }

    async def upload_objects_batch(
        self,
        objects: List[Dict[str, Any]],
        collection_name: str = "Machinery",
        tenant: Optional[str] = None
    ) -> int:
        """
        Upload objects to Weaviate in batches with multi-tenancy support

        Args:
            objects: List of object dictionaries
            collection_name: Weaviate collection name (default: "Machinery")
            tenant: Optional tenant name for multi-tenancy

        Returns:
            Number of objects uploaded successfully
        """
        from app.config import get_settings
        settings = get_settings()

        if not objects:
            return 0

        try:
            # Ensure tenant exists if multi-tenancy is enabled
            if settings.enable_weaviate_multitenancy and tenant:
                try:
                    await self.weaviate_service.create_tenant(collection_name, tenant)
                    logger.debug(f"Ensured tenant '{tenant}' exists in {collection_name}")
                except Exception as e:
                    logger.debug(f"Tenant '{tenant}' may already exist: {e}")

            result = await self.weaviate_service.batch_upsert(
                objects=objects,
                collection_name=collection_name,
                tenant=tenant if settings.enable_weaviate_multitenancy else None,
                batch_size=1000  # Weaviate supports 1000 objects per batch (10x Pinecone!)
            )

            uploaded = result.get("success", 0)
            self.stats.vectors_uploaded += uploaded

            logger.info(
                f"Uploaded {uploaded} objects to Weaviate collection '{collection_name}'"
                + (f" (tenant: {tenant})" if tenant else "")
            )
            return uploaded

        except Exception as e:
            logger.error(f"Error uploading objects to Weaviate: {e}", exc_info=True)
            # Add to errors
            for obj in objects:
                self.stats.errors.append({
                    "machine_id": obj.get("id", "unknown"),
                    "error": str(e),
                    "type": "upload"
                })
            return 0


    async def ingest_from_dict(
        self,
        machinery_data: Dict[str, Dict],
        batch_size: int = 20,
        clear_existing: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Ingest machinery data from dictionary (for API endpoint)

        This method accepts pre-parsed machinery data and processes it
        for upload to Pinecone. It's designed for use with the REST API
        where the JSON has already been parsed from an uploaded file.

        Args:
            machinery_data: Parsed JSON dictionary with machinery data
            batch_size: Number of machines to process per embedding batch
            clear_existing: Whether to delete existing vectors first
            progress_callback: Optional callback for progress updates (current, total, message)

        Returns:
            Dictionary with ingestion results:
                {
                    "total": int,
                    "successful": int,
                    "failed": int,
                    "unique_ecodes": int,
                    "embedding_tokens": int,
                    "vectors_uploaded": int,
                    "errors": List[Dict]
                }

        Raises:
            Exception: If ingestion fails critically

        Example:
            ```python
            result = await service.ingest_from_dict(
                machinery_data={"machine1": {...}},
                clear_existing=True,
                progress_callback=lambda curr, total, msg: print(f"{curr}/{total}: {msg}")
            )
            ```
        """
        logger.info("=" * 60)
        logger.info("Machinery Data Ingestion (from dictionary)")
        logger.info("=" * 60)

        # Extract devices from top-level structure if needed
        # Support both formats:
        # 1. {"devices": {...}, "metadata": {...}}  (new format)
        # 2. {"machine_id": {...}}  (legacy format)
        if "devices" in machinery_data and isinstance(machinery_data.get("devices"), dict):
            logger.info("Detected structured format with 'devices' key, extracting devices...")
            machinery_data = machinery_data["devices"]

        # Reset stats
        self.stats = IngestionStats()
        self.stats.total_machines = len(machinery_data)

        try:
            # Report progress
            if progress_callback:
                progress_callback(0, self.stats.total_machines, "Validating machinery data...")

            logger.info(f"Processing {self.stats.total_machines} machines from dictionary")

            # Phase 1: Validate and parse machines
            logger.info("Phase 1: Validating and parsing machine data...")
            machines = []

            for machine_id, machine_data_item in machinery_data.items():
                parsed = self.parse_machine(machine_id, machine_data_item)
                if parsed:
                    machines.append(parsed)
                    self.stats.successful += 1
                else:
                    self.stats.failed += 1

                self.stats.processed += 1

                # Progress callback every 50 machines
                if progress_callback and self.stats.processed % 50 == 0:
                    progress_callback(
                        self.stats.processed,
                        self.stats.total_machines,
                        f"Parsing machines... {self.stats.processed}/{self.stats.total_machines}"
                    )

            logger.info(f"Successfully parsed {len(machines)} machines")
            logger.info(f"Found {len(self.stats.unique_ecodes)} unique E-codes")

            # Phase 2: Clear existing objects if requested
            if clear_existing:
                if progress_callback:
                    progress_callback(
                        self.stats.processed,
                        self.stats.total_machines,
                        "Clearing existing machinery data from Weaviate..."
                    )

                logger.info("Phase 2: Clearing existing objects from 'Machinery' collection...")
                try:
                    await self.weaviate_service.delete_all_in_collection("Machinery")
                    logger.info("Cleared existing objects")
                except Exception as e:
                    logger.warning(f"Could not clear existing objects: {e}")

            # Phase 3: Generate embeddings in batches
            logger.info(f"Phase 3: Generating embeddings (batch_size={batch_size})...")
            machine_embeddings = []

            total_batches = (len(machines) + batch_size - 1) // batch_size

            for i in range(0, len(machines), batch_size):
                batch = machines[i:i + batch_size]
                batch_num = i // batch_size + 1

                if progress_callback:
                    progress_callback(
                        i,
                        len(machines),
                        f"Creating embeddings... batch {batch_num}/{total_batches}"
                    )

                logger.info(f"Processing embedding batch {batch_num}/{total_batches}...")

                batch_results = await self.generate_embeddings_batch(batch)
                machine_embeddings.extend(batch_results)

            logger.info(f"Generated {len(machine_embeddings)} embeddings ({self.stats.embedding_tokens:,} tokens)")

            # Phase 4: Upload to Weaviate in batches
            logger.info("Phase 4: Uploading objects to Weaviate...")
            all_objects = [
                self.create_weaviate_object(machine, embedding)
                for machine, embedding in machine_embeddings
            ]

            # Upload using Weaviate batch_upsert (supports 1000 objects per batch!)
            if progress_callback:
                progress_callback(
                    0,
                    len(all_objects),
                    "Uploading objects to Weaviate..."
                )

            logger.info(f"Uploading {len(all_objects)} objects to Weaviate Machinery collection...")
            await self.upload_objects_batch(all_objects, collection_name="Machinery")

            # Final progress callback
            if progress_callback:
                progress_callback(
                    len(all_objects),
                    len(all_objects),
                    "Ingestion complete!"
                )

            # Summary
            logger.info("=" * 60)
            logger.info("Ingestion Summary")
            logger.info("=" * 60)
            logger.info(f"  Total machines: {self.stats.total_machines}")
            logger.info(f"  Successfully processed: {self.stats.successful}")
            logger.info(f"  Failed: {self.stats.failed}")
            logger.info(f"  Unique E-codes: {len(self.stats.unique_ecodes)}")
            logger.info(f"  Embedding tokens: {self.stats.embedding_tokens:,}")
            logger.info(f"  Vectors uploaded: {self.stats.vectors_uploaded}")

            if self.stats.errors:
                logger.warning(f"Errors: {len(self.stats.errors)}")

            logger.info("=" * 60)
            logger.info("Ingestion complete!")
            logger.info("=" * 60)

            # Return results
            return {
                "total": self.stats.total_machines,
                "successful": self.stats.successful,
                "failed": self.stats.failed,
                "unique_ecodes": len(self.stats.unique_ecodes),
                "embedding_tokens": self.stats.embedding_tokens,
                "vectors_uploaded": self.stats.vectors_uploaded,
                "errors": self.stats.errors[:10],  # Return first 10 errors only
            }

        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            self.stats.errors.append({
                "machine_id": "GLOBAL",
                "error": str(e),
                "type": "fatal"
            })
            raise


# Singleton instance
_data_ingestion_service = None


def get_data_ingestion_service() -> DataIngestionService:
    """Get singleton data ingestion service instance"""
    global _data_ingestion_service
    if _data_ingestion_service is None:
        _data_ingestion_service = DataIngestionService()
    return _data_ingestion_service
