"""
Unified retrieval schemas for Phase 3 Advanced RAG pipeline.

This module defines Pydantic models for data flow through the RAG pipeline:
- Hybrid retrieval from multiple sources (Pinecone, Neo4j)
- Reranking with Cohere/cross-encoder
- Context compression with GPT-4o-mini
- Context fusion and deduplication
- Answer quality validation

Author: LLM Integration Specialist
Date: 2025-11-13
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from enum import Enum


class SourceType(str, Enum):
    """Types of retrieval sources"""
    PINECONE = "pinecone"  # Deprecated - migrated to Weaviate
    WEAVIATE = "weaviate"
    NEO4J = "neo4j"
    MULTI_QUERY = "multi_query"
    HYBRID = "hybrid"


class RetrievalSource(BaseModel):
    """
    Source of retrieved information

    Tracks where each piece of information came from for:
    - Transparency (showing users the source)
    - Debugging (tracking which sources work best)
    - Analytics (measuring source quality over time)
    """
    type: SourceType
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class RetrievalResult(BaseModel):
    """
    Unified retrieval result from any source

    Standardizes results from different retrieval systems:
    - Pinecone: Vector similarity search results
    - Neo4j: Knowledge graph query results
    - Multi-Query: Expanded query results
    """
    content: str
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0-1)")
    source: RetrievalSource
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_id: Optional[str] = None
    machine_id: Optional[str] = None

    def __hash__(self):
        """Allow deduplication in sets"""
        return hash((self.content, self.chunk_id, self.machine_id))


class HybridRetrievalResult(BaseModel):
    """
    Combined results from multiple retrieval sources

    Aggregates parallel retrieval from:
    - Pinecone (vector search)
    - Neo4j (knowledge graph)
    - Multi-query variations
    """
    query: str
    pinecone_results: List[RetrievalResult] = Field(default_factory=list)
    neo4j_results: List[RetrievalResult] = Field(default_factory=list)
    total_results: int = Field(ge=0)
    sources_used: List[str]
    retrieval_time_ms: float = Field(ge=0.0)
    source_diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    coverage_summary: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def all_results(self) -> List[RetrievalResult]:
        """
        Return an interleaved list of results to keep KG facts visible.

        Simply concatenating would push Neo4j evidence to the end; alternating
        ensures downstream prompts always see both sources.
        """
        if not self.pinecone_results:
            return list(self.neo4j_results)

        if not self.neo4j_results:
            return list(self.pinecone_results)

        blended: List[RetrievalResult] = []
        i = j = 0

        while i < len(self.pinecone_results) or j < len(self.neo4j_results):
            if j < len(self.neo4j_results):
                blended.append(self.neo4j_results[j])
                j += 1
            if i < len(self.pinecone_results):
                blended.append(self.pinecone_results[i])
                i += 1

        return blended


class RerankingMethod(str, Enum):
    """Methods used for reranking"""
    COHERE = "cohere"
    CROSS_ENCODER = "cross_encoder"
    SEMANTIC = "semantic"
    FALLBACK = "fallback"


class RankedResult(BaseModel):
    """
    Result after reranking

    Reranking improves initial retrieval by:
    - Using more sophisticated relevance models
    - Considering query-passage interaction
    - Applying cross-attention mechanisms
    """
    content: str
    original_score: float = Field(ge=0.0, le=1.0)
    rerank_score: float = Field(ge=0.0, le=1.0)
    score_improvement: float
    rank: int = Field(ge=1, description="Final rank position (1-based)")
    source: RetrievalSource
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reranking_method: RerankingMethod
    chunk_id: Optional[str] = None
    machine_id: Optional[str] = None

    class Config:
        use_enum_values = True


class RerankingResult(BaseModel):
    """
    Complete reranking output

    Contains:
    - Reranked results in optimal order
    - Performance metrics
    - Method used (for A/B testing)
    """
    query: str
    results: List[RankedResult]
    method_used: RerankingMethod
    reranking_time_ms: float = Field(ge=0.0)
    avg_score_improvement: float
    total_reranked: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        use_enum_values = True


class CompressionMethod(str, Enum):
    """Context compression methods"""
    GPT4O_MINI = "gpt4o_mini"
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"


class CompressedContext(BaseModel):
    """
    Compressed context for LLM

    Reduces token count while preserving key information:
    - Removes redundancy
    - Extracts core facts
    - Maintains semantic meaning

    Target: 65% compression (10k -> 3.5k tokens)
    """
    original_text: str
    compressed_text: str
    original_tokens: int = Field(ge=0)
    compressed_tokens: int = Field(ge=0)
    compression_ratio: float = Field(ge=0.0, le=1.0, description="% reduction")
    extracted_passages: List[str] = Field(default_factory=list)
    method_used: CompressionMethod
    compression_time_ms: float = Field(ge=0.0)
    quality_preserved: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        use_enum_values = True


class FusedContext(BaseModel):
    """
    Fused and deduplicated context

    Intelligently combines multiple sources:
    - Removes duplicate information
    - Maintains source diversity
    - Optimizes information density
    - Preserves source attribution
    """
    text: str
    sources: List[RetrievalSource]
    total_results: int = Field(ge=0)
    deduplicated_count: int = Field(ge=0, description="Number of duplicates removed")
    diversity_score: float = Field(ge=0.0, le=1.0, description="Source diversity")
    fusion_time_ms: float = Field(ge=0.0)
    token_count: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QualityIssue(str, Enum):
    """Types of quality issues"""
    INCOMPLETE = "incomplete"
    HALLUCINATION = "hallucination"
    OFF_TOPIC = "off_topic"
    UNSUPPORTED = "unsupported"
    CONTRADICTORY = "contradictory"
    LOW_CONFIDENCE = "low_confidence"


class QualityScore(BaseModel):
    """
    Answer quality validation scores

    Multi-dimensional quality assessment:
    - Completeness: Does it fully answer the question?
    - Faithfulness: Is it supported by the context?
    - Relevance: Is it on-topic?
    - Hallucination risk: Is information invented?

    Prevents poor answers from reaching users.
    """
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall quality (0-1)")
    completeness: float = Field(ge=0.0, le=1.0, description="Answers the question?")
    faithfulness: float = Field(ge=0.0, le=1.0, description="Supported by context?")
    relevance: float = Field(ge=0.0, le=1.0, description="On-topic?")
    hallucination_risk: float = Field(ge=0.0, le=1.0, description="Risk score (lower better)")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence")

    issues: List[QualityIssue] = Field(default_factory=list)
    passed: bool = Field(description="Meets quality threshold?")
    threshold_used: float = Field(default=0.7, ge=0.0, le=1.0)
    validation_time_ms: float = Field(ge=0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        use_enum_values = True


class RAGPipelineMetrics(BaseModel):
    """
    End-to-end pipeline performance metrics

    Tracks performance across all Phase 3 components:
    - Latency breakdown by stage
    - Quality metrics
    - Cost metrics (tokens, API calls)
    - Success rates
    """
    query: str

    # Latency metrics (ms)
    retrieval_time_ms: float = Field(ge=0.0)
    reranking_time_ms: float = Field(ge=0.0)
    compression_time_ms: float = Field(ge=0.0)
    fusion_time_ms: float = Field(ge=0.0)
    generation_time_ms: float = Field(ge=0.0)
    validation_time_ms: float = Field(ge=0.0)
    total_time_ms: float = Field(ge=0.0)

    # Quality metrics
    retrieval_count: int = Field(ge=0)
    reranked_count: int = Field(ge=0)
    compression_ratio: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)

    # Cost metrics
    tokens_before_compression: int = Field(ge=0)
    tokens_after_compression: int = Field(ge=0)
    tokens_saved: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)

    # Success indicators
    retrieval_success: bool
    reranking_success: bool
    compression_success: bool
    validation_passed: bool

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RAGPipelineResult(BaseModel):
    """
    Complete RAG pipeline result

    End-to-end result containing:
    - Retrieved context
    - Generated answer
    - Quality scores
    - Performance metrics
    - Source attributions
    """
    query: str
    answer: str
    context: FusedContext
    quality_score: QualityScore
    metrics: RAGPipelineMetrics
    sources: List[RetrievalSource]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional debugging info (not sent to user)
    debug_info: Optional[Dict[str, Any]] = None
