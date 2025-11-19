"""
Rate Limiting Middleware

Prevents abuse and manages API costs through user-based rate limiting.

Features:
- Per-user rate limits (hourly and daily)
- Different tiers (anonymous, regular, admin)
- In-memory storage for development
- Redis-ready for production
- Graceful error responses with Retry-After headers

Author: Claude Code
Date: 2025-11-13
"""

import logging
import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class InMemoryRateLimitStore:
    """
    In-memory rate limit storage

    Simple, thread-safe storage for development.
    For production, replace with RedisRateLimitStore.
    """

    def __init__(self):
        """Initialize store"""
        self.store: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.reset_times: Dict[str, float] = {}
        logger.info("InMemoryRateLimitStore initialized")

    def increment(self, key: str, ttl: int) -> int:
        """
        Increment counter for key

        Args:
            key: Rate limit key
            ttl: Time to live in seconds

        Returns:
            Current count
        """
        current_time = time.time()

        # Check if key expired
        if key in self.reset_times:
            if current_time >= self.reset_times[key]:
                # Reset counter
                self.store[key] = defaultdict(int)
                self.reset_times[key] = current_time + ttl

        # Set initial reset time
        if key not in self.reset_times:
            self.reset_times[key] = current_time + ttl

        # Increment
        self.store[key]["count"] += 1
        return self.store[key]["count"]

    def get(self, key: str) -> int:
        """
        Get current count for key

        Args:
            key: Rate limit key

        Returns:
            Current count
        """
        return self.store.get(key, {}).get("count", 0)

    def get_reset_time(self, key: str) -> float:
        """
        Get reset timestamp for key

        Args:
            key: Rate limit key

        Returns:
            Unix timestamp when counter resets
        """
        return self.reset_times.get(key, time.time())


class RateLimiter:
    """
    Rate limiter with tiered limits

    Limits:
    - Anonymous: 10 queries/hour, 100 queries/day
    - Regular: 100 queries/hour, 1000 queries/day
    - Admin: Unlimited

    Usage:
        rate_limiter = RateLimiter()
        await rate_limiter.check_limit(user_id, user_level)
    """

    def __init__(self, store: Optional[InMemoryRateLimitStore] = None):
        """
        Initialize rate limiter

        Args:
            store: Storage backend (default: InMemoryRateLimitStore)
        """
        self.store = store or InMemoryRateLimitStore()

        # Rate limits per user level
        self.limits = {
            "anonymous": {"hour": 10, "day": 100},
            "regular": {"hour": 100, "day": 1000},
            "admin": {"hour": None, "day": None},  # Unlimited
        }

        # Time windows
        self.ttl = {
            "hour": 3600,  # 1 hour
            "day": 86400,  # 24 hours
        }

        logger.info(f"RateLimiter initialized with limits: {self.limits}")

    def _get_hour_key(self, user_id: str) -> str:
        """Get hourly rate limit key"""
        current_hour = int(time.time() // 3600)
        return f"ratelimit:{user_id}:hour:{current_hour}"

    def _get_day_key(self, user_id: str) -> str:
        """Get daily rate limit key"""
        current_day = datetime.now().strftime("%Y-%m-%d")
        return f"ratelimit:{user_id}:day:{current_day}"

    async def check_limit(
        self,
        user_id: str,
        user_level: str = "regular"
    ) -> Dict[str, int]:
        """
        Check if user is within rate limits

        Args:
            user_id: User identifier
            user_level: User level ("anonymous", "regular", "admin")

        Returns:
            Dictionary with remaining limits

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Admin users have unlimited access
        if user_level == "admin":
            return {"remaining_hour": None, "remaining_day": None}

        # Get limits for user level
        limits = self.limits.get(user_level, self.limits["regular"])

        # Check hourly limit
        hour_key = self._get_hour_key(user_id)
        hour_count = self.store.increment(hour_key, self.ttl["hour"])

        if limits["hour"] is not None and hour_count > limits["hour"]:
            reset_time = self.store.get_reset_time(hour_key)
            retry_after = int(reset_time - time.time())

            logger.warning(
                f"Hourly rate limit exceeded for user {user_id}: "
                f"{hour_count}/{limits['hour']}"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit_type": "hourly",
                    "limit": limits["hour"],
                    "retry_after": retry_after,
                    "message": f"You have exceeded the hourly limit of {limits['hour']} requests. "
                               f"Please try again in {retry_after} seconds.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Check daily limit
        day_key = self._get_day_key(user_id)
        day_count = self.store.increment(day_key, self.ttl["day"])

        if limits["day"] is not None and day_count > limits["day"]:
            reset_time = self.store.get_reset_time(day_key)
            retry_after = int(reset_time - time.time())

            logger.warning(
                f"Daily rate limit exceeded for user {user_id}: "
                f"{day_count}/{limits['day']}"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit_type": "daily",
                    "limit": limits["day"],
                    "retry_after": retry_after,
                    "message": f"You have exceeded the daily limit of {limits['day']} requests. "
                               f"Please try again in {retry_after // 3600} hours.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Return remaining limits
        remaining = {
            "remaining_hour": limits["hour"] - hour_count if limits["hour"] else None,
            "remaining_day": limits["day"] - day_count if limits["day"] else None,
            "reset_hour": int(self.store.get_reset_time(hour_key)),
            "reset_day": int(self.store.get_reset_time(day_key)),
        }

        logger.debug(
            f"Rate limit check passed for user {user_id}: "
            f"hour={hour_count}/{limits['hour']}, day={day_count}/{limits['day']}"
        )

        return remaining

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        return {
            "limits_configured": self.limits,
            "store_type": type(self.store).__name__,
        }


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
