"""
Text Chunking Service

Handles intelligent text chunking with semantic boundaries:
- Token-based sizing with tiktoken
- Sentence-aware chunking
- Configurable overlap for context preservation
"""

import logging
from typing import List
import tiktoken

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
SENTENCE_TERMINATORS = '.!?'
MIN_SENTENCE_LENGTH = 10
MIN_CHUNK_TOKENS = 10


class TextChunker:
    """
    Intelligent text chunker that maintains semantic boundaries.

    Features:
    - Token-based sizing using tiktoken
    - Sentence-aware chunking to preserve context
    - Configurable chunk overlap for context continuity
    - Automatic filtering of very small chunks
    """

    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        """
        Initialize text chunker with tokenizer.

        Args:
            model_name: OpenAI model name for tokenizer (default: gpt-4-turbo-preview)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.warning(f"Model {model_name} not found, using fallback encoding: cl100k_base")

    def chunk_text(
        self,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> List[str]:
        """
        Chunk text into segments with token-based sizing and semantic boundaries.

        Uses a sentence-based approach to maintain context and readability.
        Chunks overlap to preserve context across boundaries.

        Args:
            text: Text to chunk
            chunk_size: Target size in tokens (default: 500)
            chunk_overlap: Overlap between chunks in tokens (default: 50)

        Returns:
            List of text chunks, filtered to remove very small chunks
        """
        # Split into sentences first to maintain semantic boundaries
        sentences = self._split_into_sentences(text)

        # Group sentences into chunks
        chunks = self._group_sentences_into_chunks(sentences, chunk_size, chunk_overlap)

        # Filter out very small chunks
        chunks = [
            chunk for chunk in chunks
            if len(self.encoding.encode(chunk)) > MIN_CHUNK_TOKENS
        ]

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences based on terminators.

        Args:
            text: Text to split

        Returns:
            List of sentence strings
        """
        sentences = []
        current_sentence = []

        for char in text:
            current_sentence.append(char)
            if char in SENTENCE_TERMINATORS and len(current_sentence) > MIN_SENTENCE_LENGTH:
                sentences.append(''.join(current_sentence).strip())
                current_sentence = []

        # Add remaining text
        if current_sentence:
            sentences.append(''.join(current_sentence).strip())

        return sentences

    def _group_sentences_into_chunks(
        self,
        sentences: List[str],
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Group sentences into chunks with specified size and overlap.

        Args:
            sentences: List of sentences to group
            chunk_size: Maximum tokens per chunk
            overlap: Number of overlap tokens between chunks

        Returns:
            List of text chunks
        """
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
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    overlap
                )

                current_chunk = overlap_sentences
                current_tokens = sum(
                    len(self.encoding.encode(sent))
                    for sent in overlap_sentences
                )

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

        return chunks

    def _get_overlap_sentences(
        self,
        chunk: List[str],
        max_overlap_tokens: int
    ) -> List[str]:
        """
        Extract sentences from end of chunk for overlap.

        Args:
            chunk: Current chunk of sentences
            max_overlap_tokens: Maximum tokens for overlap

        Returns:
            List of sentences to include in overlap
        """
        overlap_sentences = []
        overlap_tokens = 0

        for sent in reversed(chunk):
            sent_tokens = len(self.encoding.encode(sent))
            if overlap_tokens + sent_tokens <= max_overlap_tokens:
                overlap_sentences.insert(0, sent)
                overlap_tokens += sent_tokens
            else:
                break

        return overlap_sentences


# Singleton instance
_text_chunker = None


def get_text_chunker() -> TextChunker:
    """Get singleton TextChunker instance."""
    global _text_chunker
    if _text_chunker is None:
        _text_chunker = TextChunker()
    return _text_chunker


# Convenience function for direct use
def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[str]:
    """
    Convenience function to chunk text.

    Args:
        text: Text to chunk
        chunk_size: Target size in tokens (default: 500)
        chunk_overlap: Overlap between chunks in tokens (default: 50)

    Returns:
        List of text chunks
    """
    chunker = get_text_chunker()
    return chunker.chunk_text(text, chunk_size, chunk_overlap)
