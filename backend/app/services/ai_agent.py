"""
Hybrid RAG AI Agent Service

Advanced RAG system with:
- Hybrid search (vector + BM25) from Weaviate
- Optional Cohere reranking for improved relevance
- Configurable search parameters (alpha)
- Multi-collection support (Documents + Machinery)
- Streaming responses via OpenAI
"""

import logging
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel, Field

from app.config import settings
from app.services.openai_service import get_openai_service
from app.services.hybrid_retrieval_orchestrator import get_hybrid_retrieval_orchestrator

logger = logging.getLogger(__name__)


class AgentDependencies(BaseModel):
    """Dependencies for AI agent"""
    openai_service: any = Field(description="OpenAI service")
    hybrid_retrieval: any = Field(description="Hybrid retrieval orchestrator")

    class Config:
        arbitrary_types_allowed = True


class AIAgent:
    """
    Hybrid RAG AI Agent for building machinery assistance

    Advanced workflow:
    1. Retrieve documents using Weaviate hybrid search (vector + BM25)
    2. Optionally apply Cohere reranking for better relevance
    3. Build prompt with retrieved context
    4. Generate response using OpenAI
    5. Stream response to user

    Features:
    - Configurable alpha parameter (vector vs keyword balance)
    - Multi-collection support (Documents + Machinery)
    - Cohere reranking for improved results
    """

    # System prompt for all queries
    SYSTEM_PROMPT = """Sie sind ein hochspezialisierter Assistent für Baumaschinen-Dokumentation und technische Informationen.

Sie helfen Benutzern bei:
- Technischen Fragen zu Baumaschinen
- Spezifikationen und Modelldetails
- Wartungsanleitungen
- Dokumentation und Handbüchern

Wenn Sie relevante Informationen in den bereitgestellten Daten finden:
- Geben Sie klare, natürliche Antworten
- Bleiben Sie bei den Fakten aus den Daten
- Seien Sie präzise und hilfreich

Wenn keine Informationen gefunden wurden:
- Sagen Sie ehrlich: "Ich habe dazu leider keine Informationen in unseren Datenbanken."

Antworten Sie immer auf Deutsch (formelle Sie-Form) und seien Sie professionell aber freundlich."""

    def __init__(self):
        """Initialize AI agent with hybrid retrieval and OpenAI services"""
        self.openai_service = get_openai_service()
        self.hybrid_retrieval = get_hybrid_retrieval_orchestrator()

        self.temperature = settings.openai_temperature
        self.max_context_tokens = 16000  # Increased from 3500 to prevent truncation

        logger.info(
            f"Hybrid RAG AI Agent initialized with model: {settings.openai_chat_model}"
        )

    async def generate_response_stream(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        authorization_level: str = "regular",
        conversation_history: Optional[List[dict]] = None,
        category: Optional[str] = None,
        alpha: Optional[float] = None,
        enable_rerank: Optional[bool] = None,
        tenant: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response using hybrid RAG

        Args:
            query: User's question
            conversation_id: Conversation ID (optional)
            authorization_level: User's authorization level
            conversation_history: Previous messages
            category: Query category (for future use)
            alpha: Hybrid search balance (0.0=keyword, 1.0=vector, None=default 0.75)
            enable_rerank: Enable Cohere reranking (None=use default)
            tenant: Username/tenant for multi-tenancy filtering in Weaviate

        Yields:
            Response tokens as they are generated
        """
        try:
            # Step 1: Retrieve relevant documents using Weaviate hybrid search
            logger.info(
                f"[Hybrid RAG] Retrieving documents for query: '{query[:50]}...' "
                f"(alpha={alpha}, rerank={enable_rerank})"
            )

            # Create a simple intent object for retrieval
            from pydantic import BaseModel as PydanticBase

            class SimpleIntent(PydanticBase):
                primary_intent: str = "search"
                confidence: float = 1.0
                requires_semantic_search: bool = True
                requires_structured_query: bool = False
                query_complexity: str = "moderate"
                expected_answer_type: str = "explanation"
                entities: list = []

            intent = SimpleIntent()

            # Retrieve using hybrid orchestrator with alpha and reranking
            hybrid_results = await self.hybrid_retrieval.retrieve_hybrid(
                query=query,
                intent=intent,
                top_k=20,
                enable_multi_query=False,
                alpha=alpha,
                enable_rerank=enable_rerank,
                tenant=tenant,
            )

            # Convert results to simple format
            retrieved_docs = []
            for result in hybrid_results.all_results:
                retrieved_docs.append({
                    'content': result.content,
                    'score': result.score,
                    'source': result.source.name if result.source else 'Unknown'
                })

            logger.info(
                f"[Hybrid RAG] Retrieved {len(retrieved_docs)} documents "
                f"(alpha={alpha or 'default'}, rerank={enable_rerank or 'default'}, "
                f"total_results={hybrid_results.total_results})"
            )

            # DIAGNOSTIC: Log if no results found
            if len(retrieved_docs) == 0:
                logger.warning(
                    f"[DIAGNOSTIC] ⚠️  NO DOCUMENTS RETRIEVED! "
                    f"Query: '{query[:100]}', "
                    f"Alpha: {alpha}, "
                    f"Rerank: {enable_rerank}, "
                    f"Tenant: {tenant}"
                )

            # Step 2: Build simple prompt with context
            context_parts = []

            if retrieved_docs:
                context_parts.append("=== VERFÜGBARE INFORMATIONEN ===\n")
                for idx, doc in enumerate(retrieved_docs[:10], 1):
                    context_parts.append(f"[Dokument {idx}] (Relevanz: {doc['score']:.2f})")
                    context_parts.append(f"Quelle: {doc['source']}")
                    context_parts.append(f"Inhalt: {doc['content']}\n")
            else:
                context_parts.append("=== KEINE INFORMATIONEN GEFUNDEN ===")
                context_parts.append("Es wurden keine relevanten Informationen gefunden.\n")

            context_parts.append(f"\n=== BENUTZERANFRAGE ===\n{query}")

            full_context = "\n".join(context_parts)

            # Truncate if too long
            token_count = self.openai_service.count_tokens(full_context)
            if token_count > self.max_context_tokens:
                logger.warning(f"Context too long ({token_count} tokens), truncating...")
                full_context = self.openai_service.truncate_text(full_context, self.max_context_tokens)

            # Step 3: Build messages
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT}
            ]

            # Add conversation history (last 5 messages)
            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # Add current query with context
            messages.append({"role": "user", "content": full_context})

            # Step 4: Stream response from OpenAI
            logger.info("[Simple RAG] Generating response...")
            async for token in self.openai_service.generate_chat_completion_stream(messages):
                yield token

        except Exception as e:
            logger.error(f"[Simple RAG] Error: {str(e)}", exc_info=True)
            yield f"Entschuldigung, es ist ein Fehler aufgetreten: {str(e)}"


# Singleton instance
_ai_agent = None


def get_ai_agent() -> AIAgent:
    """Get singleton AI agent instance"""
    global _ai_agent
    if _ai_agent is None:
        _ai_agent = AIAgent()
    return _ai_agent
