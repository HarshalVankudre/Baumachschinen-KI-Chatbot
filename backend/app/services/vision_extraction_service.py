"""
High-fidelity GPT-4 Vision extraction helper.

Splits large diagrams/photos into overlapping tiles, calls GPT-4o with strict
instructions, and stitches the responses together so each picture contributes
thousands of characters of context. Falls back to a full-image pass if the
combined text is still shorter than the configured minimum.
"""

from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import List

from PIL import Image

from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class VisionExtractionService:
    """Encapsulates GPT-4 Vision tiling and cascading extraction."""

    def __init__(self):
        self.openai_service = get_openai_service()
        self.tile_size = 1024
        self.tile_overlap = 128
        self.max_tiles = 9
        self.min_characters = 8000
        self.tile_prompt = (
            "Du analysierst Fliesse {index}/{total}. "
            "Transkribiere jeden sichtbaren Text, Messwert, Tabelle, Diagrammteil "
            "und jede Beschriftung vollständig. Gib Tabellen in Markdown zurück, "
            "liste Achsen- und Legendenbeschriftungen komplett auf und erwähne "
            "jedes Zahlenpaar exakt. Schreibe bewusst ausführlich (>1200 Zeichen)."
        )
        self.global_prompt = (
            "Extrahiere ALLES aus dem gesamten Bild. "
            "Wenn dir im vorherigen Schritt Text oder Werte entgangen sind, "
            "hole sie jetzt nach. Gliedere nach Sektionen: Überschriften, Tabellen, "
            "Diagramme, Beschriftungen, Symbole. Mindestens 8000 Zeichen, keine Zusammenfassungen."
        )
        self.vision_model = "gpt-4o"

    async def extract_detailed_description(self, image_path: str) -> str:
        """
        Run a tiled + global GPT-4 Vision pass over an image to ensure rich output.
        """
        tiles = self._split_into_tiles(image_path)
        if not tiles:
            logger.warning("Vision extraction skipped - no tiles generated for %s", image_path)
            return ""

        used_tiles = tiles[: self.max_tiles]
        descriptions: List[str] = []

        for idx, tile in enumerate(used_tiles, start=1):
            prompt = self.tile_prompt.format(index=idx, total=len(used_tiles))
            try:
                text = await self.openai_service.describe_image_bytes(
                    image_bytes=tile,
                    instruction=prompt,
                    max_tokens=2200,
                    model=self.vision_model,
                    system_prompt=(
                        "Du bist ein gewissenhafter technischer Dokumentationsanalyst. "
                        "Du wiederholst jeden Text exakt, übersetzt nichts und entfernst nichts."
                    ),
                )
                descriptions.append(f"[TILE {idx}/{len(used_tiles)}]\n{text.strip()}")
            except Exception as e:
                logger.error("Vision tile extraction failed (%s/%s): %s", idx, len(used_tiles), e)

        combined = "\n\n".join(descriptions).strip()

        if len(combined) < self.min_characters:
            logger.info(
                "Vision output %s chars below target (%s). Requesting global pass for %s",
                len(combined),
                self.min_characters,
                image_path,
            )
            try:
                global_text = await self.openai_service.describe_image_file(
                    image_path=image_path,
                    instruction=self.global_prompt,
                    max_tokens=4096,
                    model=self.vision_model,
                    system_prompt=(
                        "Du bist ein präziser OCR-Analyst. "
                        "Du musst jedes sichtbare Detail vollständig notieren."
                    ),
                )
                combined = f"{combined}\n\n[GLOBAL PASS]\n{global_text.strip()}".strip()
            except Exception as e:
                logger.error("Global vision pass failed for %s: %s", image_path, e)

        return combined

    def _split_into_tiles(self, image_path: str) -> List[bytes]:
        """Slice the image into overlapping PNG tiles and return them as byte arrays."""
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error("Unable to open image for tiling (%s): %s", image_path, e)
            return []

        width, height = image.size
        if width <= self.tile_size and height <= self.tile_size:
            return [self._image_to_bytes(image)]

        step = max(1, self.tile_size - self.tile_overlap)
        tiles: List[bytes] = []

        y = 0
        while y < height and len(tiles) < self.max_tiles:
            x = 0
            while x < width and len(tiles) < self.max_tiles:
                box = (
                    x,
                    y,
                    min(x + self.tile_size, width),
                    min(y + self.tile_size, height),
                )
                tile = image.crop(box)
                tiles.append(self._image_to_bytes(tile))
                x += step
            y += step

        return tiles

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        """Serialize a PIL image to PNG bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()


@lru_cache()
def get_vision_extraction_service() -> VisionExtractionService:
    """Singleton accessor for dependency injection."""
    return VisionExtractionService()
