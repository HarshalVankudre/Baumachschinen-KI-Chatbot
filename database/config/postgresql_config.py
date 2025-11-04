"""
PostgreSQL REST API Configuration
Manages API key selection based on user authorization levels
"""

import os
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AuthorizationLevel(str, Enum):
    """User authorization levels (matches MongoDB users schema)"""
    REGULAR = "regular"
    SUPERUSER = "superuser"
    ADMIN = "admin"


class PostgreSQLAPIConfig:
    """PostgreSQL REST API configuration and key management (DB-023)"""

    # API Base URL
    API_BASE_URL = os.getenv("POSTGRES_API_BASE_URL", "https://api.company.com/machinery")

    # API Keys by Access Level
    API_KEY_BASIC = os.getenv("POSTGRES_API_KEY_BASIC")
    API_KEY_ELEVATED = os.getenv("POSTGRES_API_KEY_ELEVATED")
    API_KEY_ADMIN = os.getenv("POSTGRES_API_KEY_ADMIN")

    # API Endpoints (DB-022)
    ENDPOINTS = {
        "list_machinery": "/machinery",
        "get_machinery": "/machinery/{id}",
        "search_machinery": "/machinery/search",
        "available_machinery": "/machinery/available"
    }

    # Request Headers
    API_KEY_HEADER = "X-API-Key"

    # Timeouts (seconds)
    REQUEST_TIMEOUT = 10

    def __init__(self):
        """Initialize PostgreSQL API configuration"""
        if not all([self.API_KEY_BASIC, self.API_KEY_ELEVATED, self.API_KEY_ADMIN]):
            logger.warning(
                "Not all PostgreSQL API keys are configured. "
                "Some user access levels may not work."
            )

    def get_api_key(self, authorization_level: str) -> Optional[str]:
        """
        Get API key based on user authorization level

        Args:
            authorization_level: User's authorization level

        Returns:
            API key string or None

        Raises:
            ValueError: If authorization level is invalid
        """
        level_map = {
            AuthorizationLevel.REGULAR: self.API_KEY_BASIC,
            AuthorizationLevel.SUPERUSER: self.API_KEY_ELEVATED,
            AuthorizationLevel.ADMIN: self.API_KEY_ADMIN
        }

        try:
            auth_level = AuthorizationLevel(authorization_level)
            api_key = level_map[auth_level]

            if not api_key:
                logger.error(
                    f"API key not configured for authorization level: {authorization_level}"
                )

            return api_key

        except ValueError:
            raise ValueError(
                f"Invalid authorization level: {authorization_level}. "
                f"Must be one of: {[e.value for e in AuthorizationLevel]}"
            )

    def get_headers(self, authorization_level: str) -> dict:
        """
        Get request headers with appropriate API key

        Args:
            authorization_level: User's authorization level

        Returns:
            Headers dictionary
        """
        api_key = self.get_api_key(authorization_level)

        return {
            self.API_KEY_HEADER: api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_endpoint_url(self, endpoint_key: str, **kwargs) -> str:
        """
        Get full endpoint URL with parameters

        Args:
            endpoint_key: Key from ENDPOINTS dict
            **kwargs: URL parameters (e.g., id="123")

        Returns:
            Full URL string

        Raises:
            KeyError: If endpoint_key not found
        """
        endpoint = self.ENDPOINTS.get(endpoint_key)
        if not endpoint:
            raise KeyError(f"Unknown endpoint: {endpoint_key}")

        # Format URL with parameters
        endpoint_path = endpoint.format(**kwargs)

        return f"{self.API_BASE_URL}{endpoint_path}"


# Global configuration instance
postgresql_config = PostgreSQLAPIConfig()
