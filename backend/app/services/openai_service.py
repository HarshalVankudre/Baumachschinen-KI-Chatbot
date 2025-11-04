"""
OpenAI API Service

Handles all operations with OpenAI API:
- Generate embeddings (text-embedding-3-large)
- Generate chat completions (GPT-4 Turbo)
- Token counting and management
- Streaming responses
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
import tiktoken

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService:
    """Service for OpenAI API operations"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.openai_embedding_model
        self.chat_model = settings.openai_chat_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

        # Initialize tokenizer for the chat model
        try:
            self.encoding = tiktoken.encoding_for_model(self.chat_model)
        except KeyError:
            # Fallback to cl100k_base encoding for newer models
            self.encoding = tiktoken.get_encoding("cl100k_base")

        logger.info(f"OpenAI client initialized with models: {self.chat_model}, {self.embedding_model}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (3072 dimensions for text-embedding-3-large)

        Raises:
            Exception if API call fails
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Note:
            OpenAI API supports up to 2048 texts per batch request
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings

        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {str(e)}")
            raise

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate chat completion (non-streaming)

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream response (use generate_chat_completion_stream for streaming)
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Response dictionary with content and metadata

        Example:
            response = await openai_service.generate_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is Python?"}
                ]
            )
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream
            )

            if not stream:
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                return {
                    "content": content,
                    "finish_reason": finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }

        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}")
            raise

    async def generate_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat completion

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Content tokens as they are generated

        Example:
            async for token in openai_service.generate_chat_completion_stream(messages):
                print(token, end="", flush=True)
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Token counting error: {str(e)}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4

    def count_tokens_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in a list of messages

        Args:
            messages: List of message dictionaries

        Returns:
            Total number of tokens

        Note:
            This is an approximation. The actual token count may vary slightly.
        """
        try:
            num_tokens = 0
            for message in messages:
                # Every message follows <im_start>{role/name}\n{content}<im_end>\n
                num_tokens += 4
                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(value))
            num_tokens += 2  # Every reply is primed with <im_start>assistant
            return num_tokens
        except Exception as e:
            logger.error(f"Message token counting error: {str(e)}")
            # Rough estimate
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return total_chars // 4

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text

            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        except Exception as e:
            logger.error(f"Text truncation error: {str(e)}")
            # Rough character-based truncation
            char_limit = max_tokens * 4
            return text[:char_limit]

    async def health_check(self) -> Dict[str, Any]:
        """
        Check OpenAI service health

        Returns:
            Health status
        """
        try:
            # Try a simple API call
            response = await self.client.models.list()

            return {
                "status": "healthy",
                "connected": True,
                "models": [self.chat_model, self.embedding_model]
            }

        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Singleton instance
_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get singleton OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


# Standalone functions for direct imports (used by tests)
def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text (synchronous wrapper).

    Args:
        text: Text to embed

    Returns:
        Embedding vector (3072 dimensions for text-embedding-3-large)

    Raises:
        ValueError: If text is empty
        Exception: If API call fails

    Note:
        This is a synchronous wrapper for testing. Use service.generate_embedding() for async code.
    """
    if not text:
        raise ValueError("Text cannot be empty")

    import asyncio
    service = get_openai_service()

    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(service.generate_embedding(text))


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a batch (synchronous wrapper).

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors

    Raises:
        ValueError: If texts list is empty
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")

    import asyncio
    service = get_openai_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(service.generate_embeddings_batch(texts))


def generate_chat_completion(
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate chat completion (synchronous wrapper).

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Override default temperature
        max_tokens: Override default max tokens

    Returns:
        Response dictionary with:
        - content: Generated text
        - tokens_used: Total tokens consumed
        - usage: Detailed token usage

    Raises:
        ValueError: If messages list is empty
    """
    if not messages:
        raise ValueError("Messages list cannot be empty")

    import asyncio
    service = get_openai_service()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        service.generate_chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
    )

    # Add tokens_used for backward compatibility with tests
    if "usage" in result:
        result["tokens_used"] = result["usage"]["total_tokens"]

    return result


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for

    Returns:
        Number of tokens
    """
    service = get_openai_service()
    return service.count_tokens(text)
