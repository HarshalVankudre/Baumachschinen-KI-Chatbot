"""
E-code Semantic Mapper Service

Provides bidirectional mapping between German property terms and E-codes.
Supports natural language queries by mapping user terms to standardized E-codes.

Example Mappings:
    "gewicht" → "E1730"
    "motorleistung" → "E2180"
    "klimaanlage" → "E1930"
    "breite" → "E1330"

Supports:
- German synonyms: "leistung", "power", "motor power" → "E2180"
- English terms: "weight", "power", "width"
- Fuzzy matching for similar terms
- Auto-generation from all 406 E-code properties
"""

import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from difflib import get_close_matches

from app.constants import ALL_ECODE_PROPERTIES

logger = logging.getLogger(__name__)


@dataclass
class ECodeMapping:
    """
    E-code mapping with metadata

    Attributes:
        code: E-code identifier (e.g., "E1730")
        description: German description (e.g., "Gewicht")
        synonyms: List of synonyms in German and English
        category: Property category (dimension, power, feature, etc.)
    """
    code: str
    description: str
    synonyms: List[str]
    category: str


class ECodeMapper:
    """
    Semantic mapper for E-codes

    Maps natural language property queries to standardized E-codes used in
    the machinery knowledge graph. Supports German and English terms with
    synonym matching.
    """

    # E-code pattern: Exxxx - Description [unit]
    ECODE_PATTERN = re.compile(r'^(E\d+)\s*-\s*(.+?)(?:\s*\[(.+?)\])?$')

    def __init__(self):
        """Initialize E-code mapper with auto-generated mappings from all 406 properties"""
        self.mappings: Dict[str, ECodeMapping] = {}
        self.term_to_code: Dict[str, str] = {}  # Flattened for fast lookup
        self._initialize_mappings()

    def _generate_synonyms(self, description: str) -> List[str]:
        """
        Auto-generate synonyms for an E-code description

        Args:
            description: German description (e.g., "Gewicht", "Motor - Leistung")

        Returns:
            List of synonyms in German and English
        """
        synonyms = []

        # Normalize description
        desc_lower = description.lower().strip()

        # Add the description itself
        synonyms.append(desc_lower)

        # Remove special characters for alternate form
        desc_simple = re.sub(r'[^\w\s-]', '', desc_lower)
        if desc_simple != desc_lower:
            synonyms.append(desc_simple)

        # Common German to English translations
        translations = {
            # Dimensions
            "breite": ["width", "wide"],
            "länge": ["length", "long"],
            "laenge": ["length", "long"],
            "höhe": ["height", "high"],
            "hoehe": ["height", "high"],
            "tiefe": ["depth", "deep"],

            # Weight
            "gewicht": ["weight", "mass"],
            "ballast": ["ballast", "counterweight"],
            "nutzlast": ["payload", "load capacity"],
            "tragkraft": ["capacity", "load capacity", "lifting capacity"],

            # Power
            "leistung": ["power", "output", "performance"],
            "motorleistung": ["engine power", "motor power"],
            "motor": ["engine", "motor"],
            "diesel": ["diesel"],
            "benzin": ["gasoline", "petrol", "gas"],

            # Features
            "klimaanlage": ["air conditioning", "ac", "climate control"],
            "kabine": ["cabin", "cab"],
            "heizung": ["heating", "heater"],
            "funkfernsteuerung": ["radio remote control", "remote control"],

            # Operation
            "geschwindigkeit": ["speed", "velocity"],
            "drehzahl": ["rpm", "rotational speed"],
            "druck": ["pressure"],

            # Hydraulics
            "hydraulik": ["hydraulics", "hydraulic"],
            "öl": ["oil"],
            "oel": ["oil"],

            # Mobility
            "achser": ["axle"],
            "rad": ["wheel", "wheeled"],
            "kette": ["track", "crawler"],
            "reifen": ["tire", "tyre"],

            # Capacity
            "volumen": ["volume", "capacity"],
            "inhalt": ["content", "capacity", "volume"],
            "durchsatz": ["throughput", "capacity"],

            # Misc
            "schnellwechsler": ["quick coupler", "quick hitch"],
            "ausleger": ["boom", "arm"],
        }

        # Check if description contains translatable terms
        for german, english_list in translations.items():
            if german in desc_lower:
                synonyms.extend(english_list)

        # Handle compound terms (e.g., "Motor - Leistung" → "motorleistung")
        if " - " in desc_lower:
            compound = desc_lower.replace(" - ", "")
            synonyms.append(compound)
            compound_nospace = desc_lower.replace(" - ", " ").replace(" ", "")
            synonyms.append(compound_nospace)

        # Remove duplicates and empty strings
        synonyms = list(set(filter(None, synonyms)))

        return synonyms

    def _categorize_ecode(self, code: str, description: str) -> str:
        """
        Auto-categorize E-code based on description

        Args:
            code: E-code (e.g., "E1730")
            description: German description

        Returns:
            Category string
        """
        desc_lower = description.lower()

        # Dimension keywords
        if any(word in desc_lower for word in ["breite", "länge", "höhe", "tiefe", "ausladung", "ausleger"]):
            return "dimension"

        # Weight keywords
        if any(word in desc_lower for word in ["gewicht", "ballast", "nutzlast", "tragkraft", "stützlast"]):
            return "weight"

        # Power keywords
        if any(word in desc_lower for word in ["motor", "leistung", "benzin", "diesel"]):
            return "power"

        # Hydraulic keywords
        if any(word in desc_lower for word in ["hydraulik", "druck", "öl"]):
            return "hydraulics"

        # Capacity keywords
        if any(word in desc_lower for word in ["volumen", "inhalt", "durchsatz", "kapazität", "förder"]):
            return "capacity"

        # Operation keywords
        if any(word in desc_lower for word in ["geschwindigkeit", "drehzahl", "steig"]):
            return "operation"

        # Mobility keywords
        if any(word in desc_lower for word in ["achser", "rad", "kette", "reifen", "mobil"]):
            return "mobility"

        # Feature keywords
        if any(word in desc_lower for word in ["klimaanlage", "kabine", "heizung", "funk", "automatisch"]):
            return "feature"

        # Attachment keywords
        if any(word in desc_lower for word in ["schnellwechsler", "ausleger", "schild", "verdichter"]):
            return "attachments"

        # Emissions keywords
        if any(word in desc_lower for word in ["abgas", "emission", "filter"]):
            return "emissions"

        # Default
        return "general"

    def _initialize_mappings(self):
        """
        Initialize E-code mappings by auto-generating from ALL_ECODE_PROPERTIES

        Dynamically generates synonyms and categories for all 406 E-code properties.
        """
        # Auto-generate mappings from constants
        auto_generated = []

        for property_str in ALL_ECODE_PROPERTIES:
            # Skip non-E-code properties
            if not property_str.startswith("E"):
                continue

            # Parse E-code property
            match = self.ECODE_PATTERN.match(property_str)
            if not match:
                continue

            code = match.group(1)  # E-code (e.g., "E1730")
            description = match.group(2)  # Description (e.g., "Gewicht")

            # Generate synonyms
            synonyms = self._generate_synonyms(description)

            # Auto-categorize
            category = self._categorize_ecode(code, description)

            # Create mapping
            mapping = ECodeMapping(
                code=code,
                description=description,
                synonyms=synonyms,
                category=category
            )

            auto_generated.append(mapping)

        # Build mappings dictionary and term index
        for mapping in auto_generated:
            self.mappings[mapping.code] = mapping

            # Index all synonyms and description
            terms = [mapping.description.lower()] + [s.lower() for s in mapping.synonyms]
            for term in terms:
                self.term_to_code[term] = mapping.code

        logger.info(f"Initialized E-code mapper with {len(self.mappings)} codes and {len(self.term_to_code)} searchable terms")

    def add_mapping(self, mapping: ECodeMapping) -> None:
        """
        Add or update an E-code mapping

        Args:
            mapping: ECodeMapping to add

        Used by extract_ecodes.py script to add newly discovered E-codes.
        """
        self.mappings[mapping.code] = mapping

        # Update term index
        terms = [mapping.description.lower()] + [s.lower() for s in mapping.synonyms]
        for term in terms:
            self.term_to_code[term] = mapping.code

        logger.debug(f"Added mapping for {mapping.code}: {mapping.description}")

    def get_code_for_term(self, term: str, fuzzy: bool = True) -> Optional[str]:
        """
        Get E-code for a given term (German or English)

        Args:
            term: Property term (e.g., "gewicht", "power", "breite")
            fuzzy: Enable fuzzy matching for similar terms

        Returns:
            E-code string or None if not found

        Examples:
            >>> mapper.get_code_for_term("gewicht")
            "E1730"

            >>> mapper.get_code_for_term("motorleistung")
            "E2180"

            >>> mapper.get_code_for_term("weight")
            "E1730"
        """
        term_lower = term.lower().strip()

        # Exact match
        if term_lower in self.term_to_code:
            return self.term_to_code[term_lower]

        # Fuzzy match
        if fuzzy:
            matches = get_close_matches(term_lower, self.term_to_code.keys(), n=1, cutoff=0.8)
            if matches:
                matched_term = matches[0]
                logger.info(f"Fuzzy matched '{term}' → '{matched_term}' → {self.term_to_code[matched_term]}")
                return self.term_to_code[matched_term]

        logger.debug(f"No E-code found for term: {term}")
        return None

    def get_codes_for_terms(self, terms: List[str], fuzzy: bool = True) -> Dict[str, Optional[str]]:
        """
        Get E-codes for multiple terms

        Args:
            terms: List of property terms
            fuzzy: Enable fuzzy matching

        Returns:
            Dictionary mapping terms to E-codes (None if not found)

        Example:
            >>> mapper.get_codes_for_terms(["gewicht", "leistung", "breite"])
            {"gewicht": "E1730", "leistung": "E2180", "breite": "E1330"}
        """
        return {term: self.get_code_for_term(term, fuzzy=fuzzy) for term in terms}

    def get_mapping(self, code: str) -> Optional[ECodeMapping]:
        """
        Get complete mapping for an E-code

        Args:
            code: E-code identifier (e.g., "E1730")

        Returns:
            ECodeMapping or None if not found
        """
        return self.mappings.get(code)

    def get_description(self, code: str) -> Optional[str]:
        """
        Get German description for an E-code

        Args:
            code: E-code identifier

        Returns:
            German description or None

        Example:
            >>> mapper.get_description("E1730")
            "Gewicht"
        """
        mapping = self.mappings.get(code)
        return mapping.description if mapping else None

    def get_category(self, code: str) -> Optional[str]:
        """
        Get category for an E-code

        Args:
            code: E-code identifier

        Returns:
            Category string or None
        """
        mapping = self.mappings.get(code)
        return mapping.category if mapping else None

    def search_by_category(self, category: str) -> List[ECodeMapping]:
        """
        Get all E-codes in a category

        Args:
            category: Category name (dimension, power, feature, etc.)

        Returns:
            List of ECodeMapping objects

        Example:
            >>> mapper.search_by_category("power")
            [ECodeMapping(code="E2180", ...), ECodeMapping(code="E2190", ...)]
        """
        return [
            mapping for mapping in self.mappings.values()
            if mapping.category.lower() == category.lower()
        ]

    def get_all_codes(self) -> List[str]:
        """Get list of all E-codes"""
        return list(self.mappings.keys())

    def get_all_terms(self) -> List[str]:
        """Get list of all searchable terms"""
        return list(self.term_to_code.keys())

    def extract_codes_from_query(self, query: str, fuzzy: bool = True) -> Set[str]:
        """
        Extract relevant E-codes from a natural language query

        Args:
            query: Natural language query in German or English
            fuzzy: Enable fuzzy matching

        Returns:
            Set of relevant E-codes

        Example:
            >>> mapper.extract_codes_from_query("Welche Maschinen haben eine Motorleistung über 150 kW?")
            {"E2180"}

            >>> mapper.extract_codes_from_query("Zeige mir alle Bagger mit Klimaanlage und GPS")
            {"E1930"}  # E-code for Klimaanlage, GPS might not be mapped
        """
        query_lower = query.lower()
        found_codes = set()

        # Check each searchable term
        for term, code in self.term_to_code.items():
            # Word boundary matching to avoid partial matches
            if f" {term} " in f" {query_lower} " or query_lower.startswith(term) or query_lower.endswith(term):
                found_codes.add(code)

        # Try fuzzy matching on query words if no exact matches
        if not found_codes and fuzzy:
            words = query_lower.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    code = self.get_code_for_term(word, fuzzy=True)
                    if code:
                        found_codes.add(code)

        logger.info(f"Extracted {len(found_codes)} E-codes from query: {list(found_codes)}")
        return found_codes

    def get_statistics(self) -> Dict[str, int]:
        """
        Get mapper statistics

        Returns:
            Dictionary with counts of codes, terms, categories
        """
        categories = set(mapping.category for mapping in self.mappings.values())

        return {
            "total_codes": len(self.mappings),
            "total_terms": len(self.term_to_code),
            "total_categories": len(categories),
            "categories": {
                category: len(self.search_by_category(category))
                for category in categories
            }
        }


# Singleton instance
_ecode_mapper = None


def get_ecode_mapper() -> ECodeMapper:
    """Get singleton E-code mapper instance"""
    global _ecode_mapper
    if _ecode_mapper is None:
        _ecode_mapper = ECodeMapper()
    return _ecode_mapper
