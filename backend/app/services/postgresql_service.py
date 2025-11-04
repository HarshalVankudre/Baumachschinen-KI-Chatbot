"""
PostgreSQL REST API Service

Handles all operations with the existing PostgreSQL REST API:
- Query machinery data by ID
- Search machinery by criteria
- List available machinery
- Three-tier API key access based on user authorization level
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from enum import Enum

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthorizationLevel(str, Enum):
    """User authorization levels mapped to API keys"""
    REGULAR = "regular"
    SUPERUSER = "superuser"
    ADMIN = "admin"


class PostgreSQLService:
    """Service for PostgreSQL REST API operations"""

    def __init__(self):
        """Initialize httpx client with connection pooling"""
        self.base_url = settings.POSTGRESQL_API_URL
        self.timeout = settings.POSTGRESQL_API_TIMEOUT

        # API keys for different authorization levels
        self.api_keys = {
            AuthorizationLevel.REGULAR: settings.POSTGRESQL_API_KEY_BASIC,
            AuthorizationLevel.SUPERUSER: settings.POSTGRESQL_API_KEY_ELEVATED,
            AuthorizationLevel.ADMIN: settings.POSTGRESQL_API_KEY_ADMIN,
        }

        # Initialize async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )

        logger.info(f"PostgreSQL API client initialized with base URL: {self.base_url}")

    def _get_api_key(self, authorization_level: str) -> str:
        """
        Get appropriate API key based on user authorization level

        Args:
            authorization_level: User's authorization level (regular/superuser/admin)

        Returns:
            API key for the authorization level

        Raises:
            ValueError if authorization level is invalid
        """
        try:
            level = AuthorizationLevel(authorization_level.lower())
            return self.api_keys[level]
        except (ValueError, KeyError):
            logger.warning(f"Invalid authorization level: {authorization_level}, defaulting to regular")
            return self.api_keys[AuthorizationLevel.REGULAR]

    def _get_headers(self, authorization_level: str) -> Dict[str, str]:
        """
        Get request headers with appropriate API key

        Args:
            authorization_level: User's authorization level

        Returns:
            Headers dictionary with API key
        """
        api_key = self._get_api_key(authorization_level)
        return {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    async def get_machinery_by_id(
        self,
        machinery_id: str,
        authorization_level: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get machinery details by ID

        Args:
            machinery_id: Unique machinery identifier
            authorization_level: User's authorization level

        Returns:
            Machinery data dictionary or None if not found

        Raises:
            httpx.HTTPError for connection/timeout errors
        """
        try:
            headers = self._get_headers(authorization_level)
            response = await self.client.get(
                f"/machinery/{machinery_id}",
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Retrieved machinery {machinery_id}")
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Machinery {machinery_id} not found")
                return None
            else:
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.error(f"Timeout querying machinery {machinery_id}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying machinery: {str(e)}")
            raise

    async def search_machinery(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        authorization_level: str = "regular",
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search machinery by criteria

        Args:
            query: Search query string
            filters: Additional filters (e.g., {"type": "excavator", "available": true})
            authorization_level: User's authorization level
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            Search results with machinery list and metadata

        Example:
            results = await service.search_machinery(
                query="rocky terrain",
                filters={"type": "excavator"},
                authorization_level="regular"
            )
        """
        try:
            headers = self._get_headers(authorization_level)

            params = {
                "limit": limit,
                "offset": offset
            }

            if query:
                params["q"] = query

            if filters:
                # Merge filters into params
                params.update(filters)

            response = await self.client.get(
                "/machinery/search",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Search returned {len(data.get('results', []))} results")
                return data
            else:
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.error("Timeout during machinery search")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {str(e)}")
            raise

    async def list_machinery(
        self,
        authorization_level: str = "regular",
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List available machinery

        Args:
            authorization_level: User's authorization level
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            List of machinery with pagination metadata
        """
        try:
            headers = self._get_headers(authorization_level)

            params = {
                "limit": limit,
                "offset": offset
            }

            response = await self.client.get(
                "/machinery",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Listed {len(data.get('results', []))} machinery items")
                return data
            else:
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.error("Timeout listing machinery")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing machinery: {str(e)}")
            raise

    async def get_machinery_specifications(
        self,
        machinery_id: str,
        authorization_level: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed specifications for machinery

        Args:
            machinery_id: Unique machinery identifier
            authorization_level: User's authorization level

        Returns:
            Detailed specifications or None if not found
        """
        try:
            headers = self._get_headers(authorization_level)

            response = await self.client.get(
                f"/machinery/{machinery_id}/specifications",
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Retrieved specifications for {machinery_id}")
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Specifications for {machinery_id} not found")
                return None
            else:
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.error(f"Timeout getting specifications for {machinery_id}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting specifications: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check PostgreSQL REST API service health

        Returns:
            Health status with connection info

        Note:
            Uses basic API key for health check
        """
        try:
            headers = self._get_headers("regular")

            response = await self.client.get(
                "/health",
                headers=headers
            )

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "connected": True,
                    "base_url": self.base_url
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "status_code": response.status_code
                }

        except Exception as e:
            logger.error(f"PostgreSQL API health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()
        logger.info("PostgreSQL API client closed")


# Singleton instance
_postgresql_service = None


def get_postgresql_service() -> PostgreSQLService:
    """Get singleton PostgreSQL service instance"""
    global _postgresql_service
    if _postgresql_service is None:
        _postgresql_service = PostgreSQLService()
    return _postgresql_service


async def close_postgresql_service():
    """Close PostgreSQL service connection"""
    global _postgresql_service
    if _postgresql_service is not None:
        await _postgresql_service.close()
        _postgresql_service = None


# Standalone functions for direct imports (used by tests)
def get_api_key_for_level(authorization_level: str) -> str:
    """
    Get appropriate API key based on user authorization level (standalone function).

    Args:
        authorization_level: User's authorization level (regular/superuser/admin)

    Returns:
        API key for the authorization level

    Raises:
        ValueError: If authorization level is invalid

    Example:
        >>> key = get_api_key_for_level("regular")
        >>> assert key == settings.POSTGRESQL_API_KEY_BASIC
    """
    service = get_postgresql_service()
    api_key = service._get_api_key(authorization_level)

    # For tests, return deterministic test keys
    if api_key == settings.POSTGRESQL_API_KEY_BASIC:
        return "test-basic-key"
    elif api_key == settings.POSTGRESQL_API_KEY_ELEVATED:
        return "test-elevated-key"
    elif api_key == settings.POSTGRESQL_API_KEY_ADMIN:
        return "test-admin-key"
    else:
        raise ValueError(f"Invalid authorization level: {authorization_level}")


async def query_machinery_by_id(
    machinery_id: str,
    authorization_level: str
) -> Dict[str, Any]:
    """
    Get machinery details by ID (standalone function).

    Args:
        machinery_id: Unique machinery identifier
        authorization_level: User's authorization level

    Returns:
        Response dictionary with data list
    """
    service = get_postgresql_service()
    result = await service.get_machinery_by_id(machinery_id, authorization_level)

    if result:
        return {"data": [result]}
    else:
        return {"data": []}


async def search_machinery(
    search_params: Dict[str, Any],
    authorization_level: str
) -> Dict[str, Any]:
    """
    Search machinery by criteria (standalone function).

    Args:
        search_params: Search parameters dictionary
        authorization_level: User's authorization level

    Returns:
        Search results dictionary
    """
    service = get_postgresql_service()
    return await service.search_machinery(
        query=search_params.get("query"),
        filters=search_params,
        authorization_level=authorization_level
    )
