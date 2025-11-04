"""
Configuration management for the Building Machinery AI Chatbot backend.
Uses Pydantic Settings for type-safe environment variable loading.
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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

    # Pinecone Configuration
    pinecone_api_key: str = Field(default="test-pinecone-key", description="Pinecone API key")
    pinecone_environment: str = Field(default="us-east-1", description="Pinecone environment")
    pinecone_index_name: str = Field(default="machinery-docs", description="Pinecone index name")

    # OpenAI Configuration
    openai_api_key: str = Field(default="test-openai-key", description="OpenAI API key")
    openai_chat_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI chat model")
    openai_embedding_model: str = Field(default="text-embedding-3-large", description="OpenAI embedding model")
    openai_max_tokens: int = Field(default=4096, description="Maximum tokens for chat completion")
    openai_temperature: float = Field(default=0.7, description="Temperature for chat completion")

    # PostgreSQL REST API Configuration
    postgresql_api_url: str = Field(default="http://test-postgresql-api.com", description="PostgreSQL REST API base URL")
    postgresql_api_key_basic: str = Field(default="test-basic-key", description="PostgreSQL API key for regular users")
    postgresql_api_key_elevated: str = Field(default="test-elevated-key", description="PostgreSQL API key for superusers")
    postgresql_api_key_admin: str = Field(default="test-admin-key", description="PostgreSQL API key for admins")
    postgresql_api_timeout: int = Field(default=10, description="PostgreSQL API timeout in seconds")

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

    def get_postgresql_api_key(self, authorization_level: str) -> str:
        """Get PostgreSQL API key based on user authorization level."""
        key_mapping = {
            "regular": self.postgresql_api_key_basic,
            "superuser": self.postgresql_api_key_elevated,
            "admin": self.postgresql_api_key_admin,
        }
        return key_mapping.get(authorization_level, self.postgresql_api_key_basic)



    # Uppercase aliases for backward compatibility with tests
    @property
    def MONGODB_URI(self) -> str:
        """Alias for mongodb_uri (uppercase for test compatibility)."""
        return self.mongodb_uri

    @property
    def DATABASE_NAME(self) -> str:
        """Alias for mongodb_database (uppercase for test compatibility)."""
        return self.mongodb_database

    @property
    def POSTGRESQL_API_URL(self) -> str:
        """Alias for postgresql_api_url (uppercase for test compatibility)."""
        return self.postgresql_api_url

    @property
    def POSTGRESQL_API_TIMEOUT(self) -> int:
        """Alias for postgresql_api_timeout (uppercase for test compatibility)."""
        return self.postgresql_api_timeout

    @property
    def POSTGRESQL_API_KEY_BASIC(self) -> str:
        """Alias for postgresql_api_key_basic (uppercase for test compatibility)."""
        return self.postgresql_api_key_basic

    @property
    def POSTGRESQL_API_KEY_ELEVATED(self) -> str:
        """Alias for postgresql_api_key_elevated (uppercase for test compatibility)."""
        return self.postgresql_api_key_elevated

    @property
    def POSTGRESQL_API_KEY_ADMIN(self) -> str:
        """Alias for postgresql_api_key_admin (uppercase for test compatibility)."""
        return self.postgresql_api_key_admin

# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
