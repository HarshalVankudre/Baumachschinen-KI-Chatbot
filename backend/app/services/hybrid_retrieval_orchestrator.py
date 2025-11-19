"""
Hybrid Retrieval Orchestrator

Advanced retrieval using Weaviate with:
- Hybrid search (vector + BM25 keyword search)
- Multi-collection querying (Documents + Machinery)
- Cohere reranking for improved relevance
- Configurable alpha parameter for search tuning
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from functools import lru_cache

from app.services.weaviate_service import weaviate_service
from app.services.openai_service import get_openai_service
from app.schemas.retrieval_schemas import (
    RetrievalResult,
    HybridRetrievalResult,
    RetrievalSource,
    SourceType,
)
from app.services.retrieval_telemetry import (
    get_retrieval_telemetry,
    RetrievalTrace,
)

logger = logging.getLogger(__name__)


class HybridRetrievalOrchestrator:
    """
    Hybrid retrieval orchestrator using Weaviate

    Workflow:
    1. Query Weaviate using hybrid search (vector + BM25)
    2. Query both Documents and Machinery collections in parallel
    3. Optionally apply Cohere reranking for improved relevance
    4. Combine and rank results by score
    5. Return unified results with telemetry

    Features:
    - Tunable alpha parameter (0.0=keyword only, 1.0=vector only, 0.75=default)
    - Multi-collection support (Documents + Machinery)
    - Cohere reranking integration
    - Performance telemetry tracking
    """

    def __init__(self):
        """Initialize retrieval services"""
        from app.config import get_settings

        self.weaviate_service = weaviate_service
        self.openai_service = get_openai_service()
        self.telemetry = get_retrieval_telemetry()
        self.settings = get_settings()

        self.max_results_per_source = 20
        self.parallel_timeout_seconds = 10.0

        # Hybrid search settings
        self.default_alpha = self.settings.default_hybrid_alpha  # 0.75 = 75% vector, 25% BM25
        self.enable_reranking = self.settings.enable_reranking

    async def retrieve_hybrid(
        self,
        query: str,
        intent: Any,
        top_k: int = 20,
        enable_multi_query: bool = False,
        alpha: Optional[float] = None,
        enable_rerank: Optional[bool] = None,
        tenant: Optional[str] = None,
    ) -> HybridRetrievalResult:
        """
        Retrieve from Weaviate using hybrid search (vector + BM25)

        Args:
            query: User query
            intent: Query intent (for future use)
            top_k: Number of results to return
            enable_multi_query: Multi-query expansion (for future use)
            alpha: Hybrid search balance (0.0=keyword, 1.0=vector, None=default 0.75)
            enable_rerank: Enable Cohere reranking (None=use settings default)
            tenant: Optional tenant filter for multi-tenancy

        Returns:
            HybridRetrievalResult with combined results from both collections
        """
        start_time = time.time()

        logger.info(
            f"[Hybrid Retrieval] Query: '{query[:50]}...' "
            f"(alpha={alpha or self.default_alpha}, rerank={enable_rerank or self.enable_reranking})"
        )

        # Retrieve from Weaviate
        weaviate_results = await self._retrieve_from_weaviate(
            query=query,
            top_k=top_k,
            alpha=alpha,
            enable_rerank=enable_rerank,
            tenant=tenant,
        )

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"[Hybrid Retrieval] Retrieved {len(weaviate_results)} results "
            f"in {elapsed_ms:.0f}ms"
        )

        result = HybridRetrievalResult(
            query=query,
            pinecone_results=weaviate_results,  # Keep field name for backward compatibility
            neo4j_results=[],
            total_results=len(weaviate_results),
            sources_used=["weaviate"] if weaviate_results else [],
            retrieval_time_ms=elapsed_ms,
            source_diversity_score=0.0,
            coverage_summary={
                "weaviate_hits": len(weaviate_results),
                "weaviate_latency_ms": round(elapsed_ms, 2),
                "alpha": alpha or self.default_alpha,
                "reranking_enabled": enable_rerank or self.enable_reranking,
            },
        )

        # Emit telemetry trace for observability
        try:
            self.telemetry.record(
                RetrievalTrace(
                    query=query,
                    pinecone_hits=len(weaviate_results),  # Keep field name for compatibility
                    neo4j_hits=0,
                    latency_ms=elapsed_ms,
                    sources=["weaviate"] if weaviate_results else [],
                    pinecone_top_ids=[
                        res.chunk_id or (res.metadata or {}).get("filename", "unknown")
                        for res in weaviate_results[:5]
                    ],
                    neo4j_machine_ids=[],
                    metadata={
                        "hybrid_search": True,
                        "alpha": alpha or self.default_alpha,
                        "reranking": enable_rerank or self.enable_reranking,
                    },
                )
            )
        except Exception as trace_error:
            logger.debug(f"Retrieval telemetry error: {trace_error}")

        return result

    async def _retrieve_from_weaviate(
        self,
        query: str,
        top_k: int,
        alpha: Optional[float] = None,
        enable_rerank: Optional[bool] = None,
        tenant: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve from Weaviate using hybrid search (vector + BM25)

        Queries both collections in parallel:
        - Documents: Technical documentation, manuals, guides
        - Machinery: Machine specifications, models, E-code properties

        Args:
            query: Original query
            top_k: Total results to return
            alpha: Hybrid search balance (None=use default)
            enable_rerank: Enable Cohere reranking (None=use default)
            tenant: Optional tenant filter

        Returns:
            List of RetrievalResult objects from both collections
        """
        try:
            # Use default settings if not specified
            alpha = alpha if alpha is not None else self.default_alpha
            enable_rerank = enable_rerank if enable_rerank is not None else self.enable_reranking

            # Query both collections in parallel using hybrid search
            docs_task = self.weaviate_service.query_hybrid(
                query=query,
                collection_name="Documents",
                alpha=alpha,
                top_k=top_k,
                tenant=tenant,
                enable_rerank=enable_rerank,
            )

            machinery_task = self.weaviate_service.query_hybrid(
                query=query,
                collection_name="Machinery",
                alpha=alpha,
                top_k=top_k,
                tenant=tenant,
                enable_rerank=enable_rerank,
            )

            # Execute in parallel
            docs_results, machinery_results = await asyncio.gather(
                docs_task,
                machinery_task,
                return_exceptions=True
            )

            # Handle errors gracefully
            if isinstance(docs_results, Exception):
                logger.error(f"Documents collection query failed: {docs_results}")
                docs_results = []
            if isinstance(machinery_results, Exception):
                logger.error(f"Machinery collection query failed: {machinery_results}")
                machinery_results = []

            # Convert to unified format
            retrieval_results = []

            # Process document results from Weaviate
            for result in docs_results:
                # Weaviate returns properties and uuid directly
                properties = result.get("properties", {})
                content = properties.get("text_content", properties.get("text", ""))

                if not content:
                    logger.warning(f"Empty content in document result: {result.get('uuid')}")
                    continue

                retrieval_results.append(
                    RetrievalResult(
                        content=content,
                        score=float(result.get("score", 0.0)),
                        source=RetrievalSource(
                            type=SourceType.WEAVIATE,
                            name="Document Database",
                            metadata={
                                "collection": "Documents",
                                "filename": properties.get("filename", "Unknown"),
                                "category": properties.get("category", "Unknown"),
                            },
                        ),
                        metadata=properties,
                        chunk_id=result.get("uuid"),
                    )
                )

            # Process machinery results from Weaviate
            for result in machinery_results:
                # Weaviate returns properties and uuid directly
                properties = result.get("properties", {})

                # Build machine info from available fields
                name = properties.get("name", "Unknown Machine")
                manufacturer = properties.get("manufacturer", "")
                model = properties.get("model", "")
                serial_number = properties.get("serial_number", "")
                inventory_number = properties.get("inventory_number", "")

                parts = []
                parts.append(f"Machine: {name}")

                if manufacturer:
                    parts.append(f"Manufacturer: {manufacturer}")
                if model:
                    parts.append(f"Model: {model}")
                if serial_number:
                    parts.append(f"Serial Number: {serial_number}")
                if inventory_number:
                    parts.append(f"Inventory Number: {inventory_number}")

                # Add E-code properties (specifications)
                specs = []
                for key, value in properties.items():
                    if key.startswith("E") and key[1:].isdigit():
                        if value:
                            specs.append(f"  {key}: {value}")

                if specs:
                    parts.append("\nSpecifications:")
                    parts.extend(specs[:20])

                machine_info = "\n".join(parts)

                if not machine_info.strip():
                    logger.warning(f"Empty content for machinery result: {result.get('uuid')}")
                    continue

                retrieval_results.append(
                    RetrievalResult(
                        content=machine_info,
                        score=float(result.get("score", 0.0)),
                        source=RetrievalSource(
                            type=SourceType.WEAVIATE,
                            name="Machinery Database",
                            metadata={
                                "collection": "Machinery",
                                "serial_number": serial_number,
                                "model": model,
                                "manufacturer": manufacturer
                            },
                        ),
                        metadata=properties,
                        chunk_id=result.get("uuid"),
                        machine_id=serial_number,
                    )
                )

            # Sort combined results by score and limit to top_k
            retrieval_results.sort(key=lambda x: x.score, reverse=True)
            retrieval_results = retrieval_results[:top_k]

            logger.info(
                f"Retrieved {len(docs_results)} from Documents, "
                f"{len(machinery_results)} from Machinery collection, "
                f"returning top {len(retrieval_results)} results"
            )

            return retrieval_results

        except Exception as e:
            logger.error(f"Weaviate hybrid retrieval failed: {e}", exc_info=True)
            return []

    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get retrieval statistics for monitoring

        Returns:
            Dict with connection status and capabilities
        """
        try:
            # Get Weaviate health status
            health = await self.weaviate_service.health_check()

            stats = {
                "weaviate_available": health.get("status") == "healthy",
                "weaviate_version": health.get("version", "unknown"),
                "hybrid_search_enabled": True,
                "reranking_enabled": self.enable_reranking,
                "default_alpha": self.default_alpha,
                "collections": health.get("collections", {}),
                "modules": health.get("modules", {}),
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get retrieval stats: {e}")
            return {
                "weaviate_available": False,
                "error": str(e),
            }


# Singleton pattern
@lru_cache()
def get_hybrid_retrieval_orchestrator() -> HybridRetrievalOrchestrator:
    """Get singleton instance of HybridRetrievalOrchestrator"""
    return HybridRetrievalOrchestrator()
