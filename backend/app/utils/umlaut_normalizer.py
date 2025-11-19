"""
Umlaut Normalizer Utility

Fixes common UTF-8 encoding issues with German umlauts that occur when
data is incorrectly encoded or decoded. Handles the specific pattern where
umlauts are represented as multi-byte sequences.

Common Issues Fixed:
- Ã¤ → ä (a-umlaut)
- Ã¶ → ö (o-umlaut)
- Ã¼ → ü (u-umlaut)
- Ã„ → Ä (capital A-umlaut)
- Ã– → Ö (capital O-umlaut)
- Ãœ → Ü (capital U-umlaut)
- ÃŸ → ß (eszett/sharp s)
- Â³ → ³ (superscript 3, used in m³)
- Â² → ² (superscript 2, used in m²)
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


# Mapping of broken UTF-8 sequences to correct German characters
UMLAUT_FIXES: Dict[str, str] = {
    # Lowercase umlauts
    "Ã¤": "ä",  # a-umlaut
    "Ã¶": "ö",  # o-umlaut
    "Ã¼": "ü",  # u-umlaut

    # Uppercase umlauts
    "Ã„": "Ä",  # capital A-umlaut
    "Ã–": "Ö",  # capital O-umlaut
    "Ãœ": "Ü",  # capital U-umlaut

    # Eszett (sharp s)
    "ÃŸ": "ß",

    # Superscripts (for units like m³, m²)
    "Â³": "³",  # superscript 3
    "Â²": "²",  # superscript 2

    # Degree symbol
    "Â°": "°",

    # Additional common encoding issues
    "Ã ": "à",
    "Ã¡": "á",
    "Ã¢": "â",
    "Ã£": "ã",
    "Ã¨": "è",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã¬": "ì",
    "Ã­": "í",
    "Ã®": "î",
    "Ã²": "ò",
    "Ã³": "ó",
    "Ã´": "ô",
    "Ã¹": "ù",
    "Ãº": "ú",
    "Ã»": "û",
}


def normalize_umlauts(text: str) -> str:
    """
    Fix broken UTF-8 encoding of German umlauts and special characters

    Args:
        text: Text potentially containing broken umlaut encoding

    Returns:
        Text with correct UTF-8 encoding

    Example:
        >>> normalize_umlauts("Gewicht [kg - Kilogramm]")
        "Gewicht [kg - Kilogramm]"

        >>> normalize_umlauts("LÃ¤nge [mm]")
        "Länge [mm]"

        >>> normalize_umlauts("Volumen [mÂ³]")
        "Volumen [m³]"
    """
    if not text:
        return text

    # Apply all umlaut fixes
    result = text
    fixes_applied = []

    for broken, correct in UMLAUT_FIXES.items():
        if broken in result:
            result = result.replace(broken, correct)
            fixes_applied.append(f"{broken} → {correct}")

    # Log if fixes were applied
    if fixes_applied:
        logger.debug(f"Applied umlaut fixes to text: {', '.join(fixes_applied[:3])}")

    return result


def normalize_dict(data: Dict, recursive: bool = True) -> Dict:
    """
    Recursively normalize umlauts in dictionary keys and string values

    Args:
        data: Dictionary potentially containing broken encoding
        recursive: Whether to recursively process nested dictionaries

    Returns:
        Dictionary with normalized strings

    Example:
        >>> normalize_dict({"LÃ¤nge": "1200 mm", "nested": {"HÃ¶he": "800 mm"}})
        {"Länge": "1200 mm", "nested": {"Höhe": "800 mm"}}
    """
    if not isinstance(data, dict):
        return data

    result = {}

    for key, value in data.items():
        # Normalize key
        normalized_key = normalize_umlauts(str(key)) if isinstance(key, str) else key

        # Normalize value
        if isinstance(value, str):
            normalized_value = normalize_umlauts(value)
        elif isinstance(value, dict) and recursive:
            normalized_value = normalize_dict(value, recursive=True)
        elif isinstance(value, list) and recursive:
            normalized_value = [
                normalize_dict(item, recursive=True) if isinstance(item, dict)
                else normalize_umlauts(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            normalized_value = value

        result[normalized_key] = normalized_value

    return result


def detect_encoding_issues(text: str) -> bool:
    """
    Detect if text contains broken UTF-8 encoding patterns

    Args:
        text: Text to check

    Returns:
        True if encoding issues detected, False otherwise

    Example:
        >>> detect_encoding_issues("Normal text")
        False

        >>> detect_encoding_issues("LÃ¤nge")
        True
    """
    if not text:
        return False

    # Check for any known broken patterns
    for broken_pattern in UMLAUT_FIXES.keys():
        if broken_pattern in text:
            return True

    return False


def validate_german_text(text: str) -> Dict[str, any]:
    """
    Validate that German text is properly encoded

    Args:
        text: Text to validate

    Returns:
        Dictionary with validation results:
        - valid: Whether text is properly encoded
        - issues_found: List of detected issues
        - suggested_fix: Text with fixes applied (if issues found)

    Example:
        >>> validate_german_text("Motor - Leistung [kW]")
        {"valid": True, "issues_found": [], "suggested_fix": None}

        >>> validate_german_text("MotorleistungÃ¤")
        {"valid": False, "issues_found": ["Ã¤"], "suggested_fix": "Motorleistungä"}
    """
    issues = []

    # Check for broken patterns
    for broken_pattern in UMLAUT_FIXES.keys():
        if broken_pattern in text:
            issues.append(broken_pattern)

    result = {
        "valid": len(issues) == 0,
        "issues_found": issues,
        "suggested_fix": normalize_umlauts(text) if issues else None
    }

    return result


def ensure_utf8_encoding(text: str) -> str:
    """
    Ensure text is properly UTF-8 encoded

    Attempts to detect and fix common encoding issues, including:
    - Latin-1 encoded as UTF-8
    - Double-encoded UTF-8
    - Broken umlaut sequences

    Args:
        text: Text to ensure proper encoding

    Returns:
        Properly encoded UTF-8 text
    """
    if not text:
        return text

    try:
        # First, try to normalize umlauts using our mapping
        normalized = normalize_umlauts(text)

        # Ensure the result is valid UTF-8
        normalized.encode('utf-8')

        return normalized

    except (UnicodeDecodeError, UnicodeEncodeError) as e:
        logger.warning(f"Encoding issue detected: {e}")

        # Try to recover by replacing invalid characters
        try:
            # Encode to UTF-8 and decode with error handling
            fixed = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            return normalize_umlauts(fixed)
        except Exception as recovery_error:
            logger.error(f"Failed to recover encoding: {recovery_error}")
            # Last resort: return original text
            return text


class UmlautNormalizer:
    """
    Context manager for normalizing umlauts in file processing

    Usage:
        with UmlautNormalizer() as normalizer:
            text = normalizer.normalize("LÃ¤nge")
            # text = "Länge"
    """

    def __init__(self):
        self.stats = {
            "texts_processed": 0,
            "fixes_applied": 0,
            "issues_detected": 0
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stats["fixes_applied"] > 0:
            logger.info(
                f"UmlautNormalizer stats: "
                f"processed={self.stats['texts_processed']}, "
                f"fixes={self.stats['fixes_applied']}, "
                f"issues={self.stats['issues_detected']}"
            )
        return False

    def normalize(self, text: str) -> str:
        """Normalize text and update statistics"""
        self.stats["texts_processed"] += 1

        if detect_encoding_issues(text):
            self.stats["issues_detected"] += 1
            normalized = normalize_umlauts(text)
            if normalized != text:
                self.stats["fixes_applied"] += 1
            return normalized

        return text

    def normalize_dict(self, data: Dict) -> Dict:
        """Normalize dictionary and update statistics"""
        return normalize_dict(data)

    def get_stats(self) -> Dict[str, int]:
        """Get normalization statistics"""
        return self.stats.copy()


# Export main functions
__all__ = [
    "normalize_umlauts",
    "normalize_dict",
    "detect_encoding_issues",
    "validate_german_text",
    "ensure_utf8_encoding",
    "UmlautNormalizer",
]
