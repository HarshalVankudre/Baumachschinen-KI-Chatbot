"""
Configuration management for the Building Machinery AI Chatbot backend.

Uses Pydantic Settings for type-safe environment variable loading with
validation and default values. All settings are loaded from environment
variables or .env file.

This module provides:
- Type-safe configuration with validation
- Environment-specific settings
- API key management with authorization levels
- Backwards compatibility aliases for tests
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All configuration is loaded from environment variables or .env file.
    Provides type safety, validation, and sensible defaults for development.

    Attributes organized by category:
    - Application: Environment, secrets, keys
    - Server: Host, port, CORS
    - Database: MongoDB
    - Vector Database: Weaviate (with multi-tenancy, hybrid search, compression)
    - AI: OpenAI models, Cohere reranking
    - External: SMTP
    - Session: Cookie configuration
    - Admin: Email notifications
    - Observability: Sentry, logging
    - Document Upload: File size and type restrictions
    - Advanced RAG: Reranking, context compression, quality validation
    - Conversational Intelligence: Memory, analytics, feedback
    - Production Excellence: Caching, resilience, rate limiting
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    environment: str = Field(default="development", description="Environment: development, staging, production, or test")
    secret_key: str = Field(default="test-secret-key-32-chars-long", description="Secret key for session signing")
    api_internal_key: str = Field(default="test-internal-key", description="Internal API key for health checks")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    allowed_origins: str = Field(default="http://localhost:3000", description="Comma-separated CORS origins")

    # MongoDB Configuration
    mongodb_uri: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
    mongodb_database: str = Field(default="building_machinery_chatbot", description="MongoDB database name")
    mongodb_min_pool_size: int = Field(default=10, description="MongoDB minimum connection pool size")
    mongodb_max_pool_size: int = Field(default=50, description="MongoDB maximum connection pool size")

    # Pinecone Configuration (DEPRECATED - Migrating to Weaviate)
    pinecone_api_key: str = Field(default="test-pinecone-key", description="Pinecone API key (deprecated)")
    pinecone_environment: str = Field(default="us-east-1", description="Pinecone environment (deprecated)")
    pinecone_index_name: str = Field(default="machinery-docs", description="Pinecone index name (deprecated)")

    # Weaviate Configuration (Vector Database)
    weaviate_host: str = Field(default="weaviate", description="Weaviate server host")
    weaviate_port: int = Field(default=8080, description="Weaviate HTTP port")
    weaviate_grpc_port: int = Field(default=50051, description="Weaviate gRPC port")
    weaviate_scheme: str = Field(default="http", description="Weaviate connection scheme (http/https)")
    weaviate_api_key: Optional[str] = Field(default=None, description="Weaviate API key (optional, for auth)")
    enable_weaviate_multitenancy: bool = Field(default=True, description="Enable multi-tenancy for data isolation")
    enable_weaviate_compression: bool = Field(default=True, description="Enable PQ compression for storage savings")
    default_hybrid_alpha: float = Field(default=0.75, description="Default hybrid search alpha (0.0=BM25, 1.0=vector)")
    weaviate_timeout: int = Field(default=30, description="Weaviate request timeout in seconds")
    weaviate_batch_size: int = Field(default=1000, description="Batch size for Weaviate upsert operations")

    # OpenAI Configuration
    openai_api_key: str = Field(default="test-openai-key", description="OpenAI API key")
    openai_chat_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI chat model")
    openai_embedding_model: str = Field(default="text-embedding-3-large", description="OpenAI embedding model")
    openai_max_tokens: int = Field(default=4096, description="Maximum tokens for chat completion")
    openai_temperature: float = Field(default=0.7, description="Temperature for chat completion")

    # Aryn/Sycamore Configuration (Automated Document Processing)
    aryn_api_key: Optional[str] = Field(default=None, description="Aryn API key for DocParse cloud service")
    use_sycamore_processor: bool = Field(default=True, description="Use Sycamore (Aryn) processor instead of Docling")
    sycamore_extract_tables: bool = Field(default=True, description="Aryn DocParse: Extract table structure (automated)")
    sycamore_use_ocr: bool = Field(default=True, description="Aryn DocParse: Enable OCR (automated)")
    sycamore_extract_images: bool = Field(default=True, description="Aryn DocParse: Extract images (automated)")
    sycamore_output_format: str = Field(default="json", description="Aryn DocParse: Output format 'json' or 'markdown'")

    # Phase 3: Advanced RAG Configuration
    enable_advanced_rag: bool = Field(default=True, description="Enable Phase 3 Advanced RAG pipeline")
    cohere_api_key: Optional[str] = Field(default=None, description="Cohere API key for reranking (optional)")
    enable_reranking: bool = Field(default=True, description="Enable result reranking")
    enable_context_compression: bool = Field(default=True, description="Enable context compression")
    enable_quality_validation: bool = Field(default=True, description="Enable answer quality validation")
    compression_target_tokens: int = Field(default=3500, description="Target tokens after compression")
    reranking_top_k: int = Field(default=10, description="Number of results to keep after reranking")
    hybrid_retrieval_top_k: int = Field(default=20, description="Number of results to retrieve per source")

    # Phase 4: Conversational Intelligence & Analytics Configuration
    enable_conversation_memory: bool = Field(default=True, description="Enable conversation memory with summarization")
    enable_analytics_tracking: bool = Field(default=True, description="Enable analytics tracking for queries")
    enable_feedback_collection: bool = Field(default=True, description="Enable user feedback collection")
    memory_summarization_interval: int = Field(default=10, description="Summarize conversation every N messages")
    memory_max_summary_tokens: int = Field(default=500, description="Maximum tokens for conversation summary")
    memory_max_context_tokens: int = Field(default=500, description="Maximum tokens for memory context in prompts")
    analytics_batch_size: int = Field(default=100, description="Batch size for analytics aggregation")
    feedback_retention_days: int = Field(default=365, description="Days to retain feedback data")

    # Phase 5: Production Excellence & User Experience Configuration
    enable_caching: bool = Field(default=True, description="Enable caching for cost reduction (70-80% savings)")
    enable_resilience: bool = Field(default=True, description="Enable retry logic and circuit breakers")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting to prevent abuse")
    cache_max_size: int = Field(default=1000, description="Maximum cache entries (LRU eviction)")
    cache_embedding_ttl: int = Field(default=86400, description="Embedding cache TTL in seconds (24 hours)")
    cache_retrieval_ttl: int = Field(default=3600, description="Retrieval cache TTL in seconds (1 hour)")
    cache_response_ttl: int = Field(default=1800, description="Response cache TTL in seconds (30 minutes)")
    retry_max_attempts: int = Field(default=3, description="Maximum retry attempts for failed API calls")
    retry_base_delay: float = Field(default=1.0, description="Base delay for exponential backoff (seconds)")
    circuit_breaker_threshold: float = Field(default=0.5, description="Failure rate to open circuit (0.0-1.0)")
    circuit_breaker_timeout: int = Field(default=30, description="Circuit breaker recovery timeout (seconds)")
    rate_limit_anonymous_hour: int = Field(default=10, description="Hourly rate limit for anonymous users")
    rate_limit_anonymous_day: int = Field(default=100, description="Daily rate limit for anonymous users")
    rate_limit_regular_hour: int = Field(default=100, description="Hourly rate limit for regular users")
    rate_limit_regular_day: int = Field(default=1000, description="Daily rate limit for regular users")

    # SMTP Configuration
    smtp_host: str = Field(default="smtp.test.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="test@test.com", description="SMTP username")
    smtp_password: str = Field(default="test-password", description="SMTP password")
    smtp_from_email: str = Field(default="noreply@test.com", description="From email address")
    smtp_from_name: str = Field(default="Building Machinery AI Support", description="From name")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # Frontend URL
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL for email links")

    # Session Configuration
    session_cookie_name: str = Field(default="session_id", description="Session cookie name")
    session_max_age_seconds: int = Field(default=2592000, description="Session max age (30 days)")
    session_remember_me_max_age_seconds: int = Field(default=2592000, description="Remember me max age")

    # Admin Configuration
    admin_email: str = Field(default="admin@test.com", description="Admin email for notifications")

    # Sentry Configuration
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    # Document Upload
    max_upload_size_mb: int = Field(default=0, description="Max upload size in MB (0 = unlimited)")
    allowed_file_extensions: str = Field(
        default=".pdf,.docx,.pptx,.xlsx,.xls,.ppt,.jpg,.jpeg,.png",
        description="Comma-separated allowed file extensions"
    )

    @field_validator("allowed_origins")
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("allowed_file_extensions")
    @classmethod
    def parse_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated extensions into a list."""
        return [ext.strip().lower() for ext in v.split(",")]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production", "test"]
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"

    # Uppercase aliases for backward compatibility with tests
    @property
    def MONGODB_URI(self) -> str:
        """Alias for mongodb_uri (uppercase for test compatibility)."""
        return self.mongodb_uri

    @property
    def DATABASE_NAME(self) -> str:
        """Alias for mongodb_database (uppercase for test compatibility)."""
        return self.mongodb_database

# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
