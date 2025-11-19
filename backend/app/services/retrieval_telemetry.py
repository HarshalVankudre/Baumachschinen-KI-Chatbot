"""
Retrieval telemetry and tracing utilities.

Keeps lightweight, in-memory traces for the most recent hybrid retrieval runs so
we can debug coverage gaps and source diversity without attaching an external
observability vendor. Emits summarized statistics to the logger and exposes the
last N traces for health endpoints.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class RetrievalTrace:
    """Single retrieval attempt summary."""

    query: str
    pinecone_hits: int
    neo4j_hits: int
    latency_ms: float
    sources: List[str]
    pinecone_top_ids: List[str] = field(default_factory=list)
    neo4j_machine_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable representation for debugging endpoints."""
        return asdict(self)


class RetrievalTelemetry:
    """
    Keeps a rolling buffer of retrieval traces and exposes aggregated metrics.

    This lightweight store makes it easy to surface hybrid-retrieval coverage
    inside /health and Prometheus scrapes without persisting sensitive context.
    """

    def __init__(self, max_traces: int = 100):
        self.max_traces = max_traces
        self._traces: List[RetrievalTrace] = []

    def record(self, trace: RetrievalTrace) -> None:
        """Append a retrieval trace and trim the buffer."""
        self._traces.append(trace)
        if len(self._traces) > self.max_traces:
            self._traces = self._traces[-self.max_traces :]

        logger.info(
            "[RAG][TRACE] %s | pinecone=%d neo4j=%d latency=%.0fms sources=%s",
            trace.query[:60],
            trace.pinecone_hits,
            trace.neo4j_hits,
            trace.latency_ms,
            trace.sources,
        )

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the N most recent traces as dicts."""
        recent = self._traces[-limit:]
        return [trace.to_dict() for trace in reversed(recent)]

    def get_stats(self) -> Dict[str, Any]:
        """Compute aggregate statistics for observability endpoints."""
        if not self._traces:
            return {
                "total_traces": 0,
                "avg_latency_ms": 0,
                "avg_pinecone_hits": 0,
                "avg_neo4j_hits": 0,
            }

        total = len(self._traces)
        avg_latency = sum(t.latency_ms for t in self._traces) / total
        avg_pinecone = sum(t.pinecone_hits for t in self._traces) / total
        avg_neo4j = sum(t.neo4j_hits for t in self._traces) / total

        return {
            "total_traces": total,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_pinecone_hits": round(avg_pinecone, 2),
            "avg_neo4j_hits": round(avg_neo4j, 2),
            "last_trace": self._traces[-1].to_dict(),
        }


@lru_cache()
def get_retrieval_telemetry() -> RetrievalTelemetry:
    """Singleton accessor."""
    return RetrievalTelemetry()
