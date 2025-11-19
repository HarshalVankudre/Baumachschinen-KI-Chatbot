"""
Property Extractor Utility for E-code Parsing

Parses and extracts machine property information from E-code format used in
the Pinecone machinery namespace. Handles German property names and units.

E-code Format Example:
    "E1730 - Gewicht [kg]" → {code: "E1730", description: "Gewicht", unit: "kg"}
    "E1930 - Klimaanlage" → {code: "E1930", description: "Klimaanlage", unit: ""}

This utility is designed to handle the variable property structure where:
- Each machine can have 5-30+ properties
- Properties use E-code prefixes (E1330, E1730, E2180, etc.)
- Units can be present [mm], [kg], [kW] or absent (for boolean/text values)
- Boolean values are "Ja"/"Nein" in German
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PropertyType(str, Enum):
    """Property value types"""
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    TEXT = "text"
    UNIT_VALUE = "unit_value"


@dataclass
class ParsedProperty:
    """
    Parsed property from E-code format

    Attributes:
        code: E-code identifier (e.g., "E1730")
        description: Property description in German (e.g., "Gewicht")
        unit: Unit of measurement (e.g., "kg", "mm", "kW") or empty string
        value: Property value (can be number, "Ja"/"Nein", or text)
        property_type: Type classification
    """
    code: str
    description: str
    unit: str
    value: str
    property_type: PropertyType


@dataclass
class DeviceInfo:
    """
    Device information extracted from machine data

    Attributes:
        name: Machine name (e.g., "MF 2500CS STG V 2019")
        serial_number: Serial number (e.g., "34532")
        inventory_number: Inventory number (can be empty)
    """
    name: str
    serial_number: str
    inventory_number: str


class PropertyExtractor:
    """
    Extract and parse machine properties from E-code format

    Handles the complex property structure of machinery data where each
    machine has a variable set of properties identified by E-codes.
    """

    # E-code pattern: "E1730 - Gewicht [kg]" or "E1930 - Klimaanlage"
    ECODE_PATTERN = re.compile(
        r'^E(\d+)\s*-\s*([^[\]]+?)(?:\s*\[([^\]]+)\])?\s*$',
        re.UNICODE
    )

    # Boolean values in German
    BOOLEAN_VALUES = {"Ja", "Nein", "ja", "nein"}

    # Common German units for classification
    NUMERIC_UNITS = {
        "mm", "cm", "m", "km",  # Length
        "kg", "t", "g",  # Weight
        "kW", "PS", "W",  # Power
        "l", "m³", "cm³",  # Volume
        "bar", "MPa",  # Pressure
        "km/h", "m/s",  # Speed
        "t/h", "m³/h",  # Flow rate
        "°C", "K",  # Temperature
        "min", "h", "s"  # Time
    }

    @classmethod
    def parse_ecode_key(cls, ecode_key: str) -> Optional[Dict[str, str]]:
        """
        Parse E-code property key into components

        Args:
            ecode_key: Property key in format "E1730 - Gewicht [kg]" or "E1930 - Klimaanlage"

        Returns:
            Dictionary with 'code', 'description', 'unit' or None if invalid

        Examples:
            >>> parse_ecode_key("E1730 - Gewicht [kg]")
            {'code': 'E1730', 'description': 'Gewicht', 'unit': 'kg'}

            >>> parse_ecode_key("E1930 - Klimaanlage")
            {'code': 'E1930', 'description': 'Klimaanlage', 'unit': ''}
        """
        match = cls.ECODE_PATTERN.match(ecode_key.strip())
        if not match:
            logger.warning(f"Invalid E-code format: {ecode_key}")
            return None

        code_number, description, unit = match.groups()

        return {
            "code": f"E{code_number}",
            "description": description.strip(),
            "unit": unit.strip() if unit else ""
        }

    @classmethod
    def classify_property_type(cls, value: str, unit: str) -> PropertyType:
        """
        Classify property type based on value and unit

        Args:
            value: Property value
            unit: Unit of measurement

        Returns:
            PropertyType classification
        """
        # Boolean type (German)
        if value.strip() in cls.BOOLEAN_VALUES:
            return PropertyType.BOOLEAN

        # Numeric with unit
        if unit and unit.split()[0] in cls.NUMERIC_UNITS:  # Split to handle "mm - Millimeter"
            try:
                float(value.replace(',', '.'))  # German decimal format
                return PropertyType.UNIT_VALUE
            except ValueError:
                return PropertyType.TEXT

        # Pure numeric
        try:
            float(value.replace(',', '.'))
            return PropertyType.NUMERIC
        except ValueError:
            return PropertyType.TEXT

    @classmethod
    def parse_property(
        cls,
        ecode_key: str,
        property_data: Dict[str, Any]
    ) -> Optional[ParsedProperty]:
        """
        Parse complete property with E-code key and value

        Args:
            ecode_key: E-code property key (e.g., "E1730 - Gewicht [kg]")
            property_data: Property value data with 'value' and 'unit' keys

        Returns:
            ParsedProperty object or None if invalid

        Example:
            >>> parse_property(
            ...     "E1730 - Gewicht [kg]",
            ...     {"value": "21000", "unit": "kg - Kilogramm"}
            ... )
            ParsedProperty(
                code="E1730",
                description="Gewicht",
                unit="kg",
                value="21000",
                property_type=PropertyType.UNIT_VALUE
            )
        """
        # Parse E-code key
        parsed_key = cls.parse_ecode_key(ecode_key)
        if not parsed_key:
            return None

        # Extract value
        value = str(property_data.get("value", "")).strip()
        if not value:
            logger.debug(f"Empty value for E-code: {ecode_key}")
            return None

        # Extract unit (prefer unit from key, fallback to data unit)
        unit_from_key = parsed_key["unit"]
        unit_from_data = property_data.get("unit", "")

        # Clean unit (remove verbose German descriptions like "mm - Millimeter")
        if unit_from_data and " - " in unit_from_data:
            unit_from_data = unit_from_data.split(" - ")[0].strip()

        # Use key unit if present, otherwise data unit
        final_unit = unit_from_key if unit_from_key else unit_from_data

        # Classify property type
        property_type = cls.classify_property_type(value, final_unit)

        return ParsedProperty(
            code=parsed_key["code"],
            description=parsed_key["description"],
            unit=final_unit,
            value=value,
            property_type=property_type
        )

    @classmethod
    def extract_device_info(cls, device_info_data: Dict[str, Any]) -> DeviceInfo:
        """
        Extract device information from machine data

        Args:
            device_info_data: Device info dictionary with name, serial_number, inventory_number

        Returns:
            DeviceInfo object

        Example:
            >>> extract_device_info({
            ...     "name": "MF 2500CS STG V 2019",
            ...     "serial_number": "34532",
            ...     "inventory_number": ""
            ... })
            DeviceInfo(
                name="MF 2500CS STG V 2019",
                serial_number="34532",
                inventory_number=""
            )
        """
        return DeviceInfo(
            name=device_info_data.get("name", "Unknown"),
            serial_number=device_info_data.get("serial_number", ""),
            inventory_number=device_info_data.get("inventory_number", "")
        )

    @classmethod
    def extract_all_properties(
        cls,
        properties_data: Dict[str, Dict[str, Any]]
    ) -> List[ParsedProperty]:
        """
        Extract all properties from machine properties dictionary

        Args:
            properties_data: Dictionary of E-code keys to property values

        Returns:
            List of ParsedProperty objects

        Example:
            >>> extract_all_properties({
            ...     "E1730 - Gewicht [kg]": {"value": "21000", "unit": "kg"},
            ...     "E2180 - Motor - Leistung [kW]": {"value": "168", "unit": "kW"},
            ...     "E1930 - Klimaanlage": {"value": "Nein", "unit": ""}
            ... })
            [ParsedProperty(...), ParsedProperty(...), ParsedProperty(...)]
        """
        parsed_properties = []

        for ecode_key, property_data in properties_data.items():
            parsed_prop = cls.parse_property(ecode_key, property_data)
            if parsed_prop:
                parsed_properties.append(parsed_prop)
            else:
                logger.debug(f"Skipped invalid property: {ecode_key}")

        logger.info(f"Extracted {len(parsed_properties)} valid properties")
        return parsed_properties

    @classmethod
    def extract_manufacturer_from_name(cls, machine_name: str) -> Optional[str]:
        """
        Attempt to extract manufacturer from machine name

        Args:
            machine_name: Full machine name

        Returns:
            Manufacturer name or None

        Examples:
            >>> extract_manufacturer_from_name("Caterpillar 320D")
            "Caterpillar"

            >>> extract_manufacturer_from_name("MF 2500CS STG V 2019")
            "MF"
        """
        # Common manufacturer patterns
        common_manufacturers = [
            "Caterpillar", "CAT", "Komatsu", "Volvo", "Liebherr",
            "Hitachi", "JCB", "Doosan", "Hyundai", "Terex",
            "Manitou", "JLG", "Genie", "Bobcat", "Case",
            "John Deere", "Wirtgen", "Hamm", "Bomag", "Dynapac",
            "Atlas Copco", "Sandvik", "MF", "Massey Ferguson"
        ]

        machine_name_upper = machine_name.upper()

        for manufacturer in common_manufacturers:
            if manufacturer.upper() in machine_name_upper:
                return manufacturer

        # Fallback: return first word if it looks like a manufacturer
        first_word = machine_name.split()[0] if machine_name else None
        if first_word and len(first_word) > 2:
            return first_word

        return None

    @classmethod
    def create_machine_id(cls, device_info: DeviceInfo) -> str:
        """
        Create unique machine ID from device info

        Args:
            device_info: DeviceInfo object

        Returns:
            Unique machine ID

        Example:
            >>> create_machine_id(DeviceInfo("MF 2500CS", "34532", "INV123"))
            "MF-2500CS-34532"
        """
        # Normalize name (remove spaces, special chars)
        normalized_name = re.sub(r'[^a-zA-Z0-9-]', '-', device_info.name)
        normalized_name = re.sub(r'-+', '-', normalized_name).strip('-')

        # Use serial number as primary identifier
        if device_info.serial_number:
            return f"{normalized_name}-{device_info.serial_number}"

        # Fallback to inventory number
        if device_info.inventory_number:
            return f"{normalized_name}-{device_info.inventory_number}"

        # Last resort: just name
        return normalized_name


# Singleton instance for convenience
_property_extractor = PropertyExtractor()


def parse_ecode_key(ecode_key: str) -> Optional[Dict[str, str]]:
    """Convenience function for parsing E-code keys"""
    return _property_extractor.parse_ecode_key(ecode_key)


def parse_property(ecode_key: str, property_data: Dict[str, Any]) -> Optional[ParsedProperty]:
    """Convenience function for parsing complete property"""
    return _property_extractor.parse_property(ecode_key, property_data)


def extract_device_info(device_info_data: Dict[str, Any]) -> DeviceInfo:
    """Convenience function for extracting device info"""
    return _property_extractor.extract_device_info(device_info_data)


def extract_all_properties(properties_data: Dict[str, Dict[str, Any]]) -> List[ParsedProperty]:
    """Convenience function for extracting all properties"""
    return _property_extractor.extract_all_properties(properties_data)
