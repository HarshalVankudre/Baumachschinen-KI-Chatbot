"""
Query Performance Monitoring Utility

Provides helpers for monitoring and logging database query performance.
"""
import logging
import time
from functools import wraps
from typing import Callable, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """Context manager for monitoring query performance"""

    def __init__(self, query_name: str, warn_threshold: float = 1.0):
        """
        Initialize query performance monitor

        Args:
            query_name: Name/description of the query being monitored
            warn_threshold: Log warning if query exceeds this many seconds (default 1.0s)
        """
        self.query_name = query_name
        self.warn_threshold = warn_threshold
        self.start_time = None
        self.duration = None

    def __enter__(self):
        """Start monitoring"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring and log results"""
        self.duration = time.time() - self.start_time

        if exc_type is not None:
            logger.error(
                f"Query '{self.query_name}' failed after {self.duration:.2f}s: {exc_val}"
            )
        elif self.duration >= self.warn_threshold:
            logger.warning(
                f"Slow query detected: '{self.query_name}' took {self.duration:.2f}s "
                f"(threshold: {self.warn_threshold}s)"
            )
        else:
            logger.debug(
                f"Query '{self.query_name}' completed in {self.duration:.2f}s"
            )

        return False  # Don't suppress exceptions


async def with_timeout(
    coro,
    timeout: float,
    operation_name: str = "operation",
    fallback_value: Optional[Any] = None,
    raise_on_timeout: bool = True
):
    """
    Execute async operation with timeout

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name for logging
        fallback_value: Value to return on timeout (if not raising)
        raise_on_timeout: Whether to raise TimeoutError or return fallback

    Returns:
        Result of coroutine or fallback_value on timeout

    Raises:
        asyncio.TimeoutError: If timeout occurs and raise_on_timeout=True
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout}s")
        if raise_on_timeout:
            raise
        return fallback_value


def log_query_performance(query_name: str, warn_threshold: float = 1.0):
    """
    Decorator for logging query performance

    Args:
        query_name: Name of the query
        warn_threshold: Log warning if query exceeds this many seconds

    Example:
        @log_query_performance("fetch_users", warn_threshold=0.5)
        async def fetch_users():
            return await db.users.find().to_list(100)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if duration >= warn_threshold:
                    logger.warning(
                        f"Slow query: '{query_name}' in {func.__name__} "
                        f"took {duration:.2f}s (threshold: {warn_threshold}s)"
                    )
                else:
                    logger.debug(
                        f"Query '{query_name}' completed in {duration:.2f}s"
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Query '{query_name}' in {func.__name__} failed "
                    f"after {duration:.2f}s: {str(e)}"
                )
                raise

        return wrapper
    return decorator


class QueryStats:
    """Simple query statistics tracker"""

    def __init__(self):
        self.queries = []
        self.total_time = 0
        self.slow_queries = []
        self.slow_threshold = 1.0

    def record(self, query_name: str, duration: float):
        """Record a query execution"""
        self.queries.append({
            "name": query_name,
            "duration": duration,
            "timestamp": time.time()
        })
        self.total_time += duration

        if duration >= self.slow_threshold:
            self.slow_queries.append({
                "name": query_name,
                "duration": duration
            })

    def get_summary(self) -> dict:
        """Get summary statistics"""
        return {
            "total_queries": len(self.queries),
            "total_time": round(self.total_time, 2),
            "average_time": round(self.total_time / len(self.queries), 2) if self.queries else 0,
            "slow_queries": len(self.slow_queries),
            "slow_query_details": self.slow_queries
        }

    def log_summary(self):
        """Log query statistics"""
        summary = self.get_summary()
        logger.info(
            f"Query Summary: {summary['total_queries']} queries, "
            f"{summary['total_time']}s total, "
            f"{summary['average_time']}s average, "
            f"{summary['slow_queries']} slow queries"
        )

        if summary['slow_queries'] > 0:
            for sq in summary['slow_query_details']:
                logger.warning(f"  - Slow query: {sq['name']} took {sq['duration']:.2f}s")
