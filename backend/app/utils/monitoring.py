"""
Performance monitoring and profiling utilities.

Provides decorators and helpers for:
- Timing slow operations
- Performance logging
- Resource usage tracking
- Query performance monitoring
"""
import time
import functools
import logging
from typing import Callable, Any, Optional, Dict
import asyncio
from contextlib import contextmanager, asynccontextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# Timing Decorator
# =============================================================================

def timing_decorator(
    operation_name: Optional[str] = None,
    log_level: str = "INFO",
    slow_threshold_seconds: float = 1.0,
    logger_instance: Optional[logging.Logger] = None
):
    """
    Decorator to measure and log execution time of functions.

    Logs warning if execution exceeds slow_threshold_seconds.

    Args:
        operation_name: Name for the operation (defaults to function name)
        log_level: Log level for normal execution
        slow_threshold_seconds: Threshold for slow operation warning
        logger_instance: Logger to use (defaults to module logger)

    Usage:
        @timing_decorator()
        def slow_function():
            time.sleep(2)

        @timing_decorator(operation_name="Database Query", slow_threshold_seconds=0.5)
        async def query_database():
            await db.find_one({})
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        log = logger_instance or logger

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time

                extra_data = {
                    'operation': op_name,
                    'duration_seconds': elapsed,
                    'is_slow': elapsed > slow_threshold_seconds
                }

                if elapsed > slow_threshold_seconds:
                    log.warning(
                        f"Slow operation: {op_name} took {elapsed:.3f}s (threshold: {slow_threshold_seconds}s)",
                        extra=extra_data
                    )
                else:
                    getattr(log, log_level.lower())(
                        f"{op_name} completed in {elapsed:.3f}s",
                        extra=extra_data
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time

                extra_data = {
                    'operation': op_name,
                    'duration_seconds': elapsed,
                    'is_slow': elapsed > slow_threshold_seconds
                }

                if elapsed > slow_threshold_seconds:
                    log.warning(
                        f"Slow operation: {op_name} took {elapsed:.3f}s (threshold: {slow_threshold_seconds}s)",
                        extra=extra_data
                    )
                else:
                    getattr(log, log_level.lower())(
                        f"{op_name} completed in {elapsed:.3f}s",
                        extra=extra_data
                    )

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# Performance Context Managers
# =============================================================================

@contextmanager
def performance_timer(operation_name: str, log_results: bool = True):
    """
    Context manager for timing code blocks.

    Usage:
        with performance_timer("Complex Calculation"):
            result = expensive_operation()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        if log_results:
            logger.info(
                f"{operation_name} completed in {elapsed:.3f}s",
                extra={'operation': operation_name, 'duration_seconds': elapsed}
            )


@asynccontextmanager
async def async_performance_timer(operation_name: str, log_results: bool = True):
    """
    Async context manager for timing async code blocks.

    Usage:
        async with async_performance_timer("API Call"):
            result = await api.fetch_data()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        if log_results:
            logger.info(
                f"{operation_name} completed in {elapsed:.3f}s",
                extra={'operation': operation_name, 'duration_seconds': elapsed}
            )


# =============================================================================
# Performance Statistics Tracker
# =============================================================================

class PerformanceTracker:
    """
    Tracks performance statistics for operations.

    Collects timing data and provides summary statistics.
    """

    def __init__(self):
        """Initialize performance tracker."""
        self.timings: Dict[str, list] = {}
        self.counts: Dict[str, int] = {}

    def record(self, operation: str, duration_seconds: float):
        """
        Record a timing measurement.

        Args:
            operation: Operation name
            duration_seconds: Duration in seconds
        """
        if operation not in self.timings:
            self.timings[operation] = []
            self.counts[operation] = 0

        self.timings[operation].append(duration_seconds)
        self.counts[operation] += 1

    def get_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            Dictionary with stats or None if no data
        """
        if operation not in self.timings or not self.timings[operation]:
            return None

        timings = self.timings[operation]
        return {
            'count': self.counts[operation],
            'total_seconds': sum(timings),
            'average_seconds': sum(timings) / len(timings),
            'min_seconds': min(timings),
            'max_seconds': max(timings),
            'p50_seconds': self._percentile(timings, 50),
            'p95_seconds': self._percentile(timings, 95),
            'p99_seconds': self._percentile(timings, 99),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        return {
            operation: self.get_stats(operation)
            for operation in self.timings.keys()
        }

    def reset(self):
        """Reset all statistics."""
        self.timings.clear()
        self.counts.clear()

    @staticmethod
    def _percentile(values: list, percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    @contextmanager
    def track(self, operation: str):
        """
        Context manager for tracking operation performance.

        Usage:
            tracker = PerformanceTracker()
            with tracker.track("database_query"):
                result = db.query()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.record(operation, elapsed)


# Global performance tracker instance
_global_tracker = PerformanceTracker()


def get_performance_tracker() -> PerformanceTracker:
    """Get global performance tracker instance."""
    return _global_tracker


# =============================================================================
# Query Performance Monitor
# =============================================================================

class QueryPerformanceMonitor:
    """
    Monitor database query performance.

    Logs slow queries and collects statistics.
    """

    def __init__(
        self,
        query_name: str,
        warn_threshold: float = 1.0,
        error_threshold: float = 5.0
    ):
        """
        Initialize query monitor.

        Args:
            query_name: Name/description of the query
            warn_threshold: Threshold for warning log (seconds)
            error_threshold: Threshold for error log (seconds)
        """
        self.query_name = query_name
        self.warn_threshold = warn_threshold
        self.error_threshold = error_threshold
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log if needed."""
        if self.start_time is None:
            return

        elapsed = time.perf_counter() - self.start_time

        extra_data = {
            'query': self.query_name,
            'duration_seconds': elapsed,
            'is_slow': elapsed > self.warn_threshold,
            'is_critical': elapsed > self.error_threshold
        }

        if elapsed > self.error_threshold:
            logger.error(
                f"CRITICAL: Very slow query '{self.query_name}' took {elapsed:.3f}s",
                extra=extra_data
            )
        elif elapsed > self.warn_threshold:
            logger.warning(
                f"Slow query: '{self.query_name}' took {elapsed:.3f}s",
                extra=extra_data
            )
        else:
            logger.debug(
                f"Query '{self.query_name}' completed in {elapsed:.3f}s",
                extra=extra_data
            )

        # Record in global tracker
        _global_tracker.record(f"query_{self.query_name}", elapsed)


# =============================================================================
# Timeout Helper
# =============================================================================

async def with_timeout(
    coro,
    timeout: float,
    operation_name: str = "operation",
    fallback_value: Any = None,
    raise_on_timeout: bool = True
):
    """
    Execute async operation with timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name for logging
        fallback_value: Value to return on timeout (if not raising)
        raise_on_timeout: Whether to raise TimeoutError

    Returns:
        Result of coroutine or fallback_value

    Raises:
        asyncio.TimeoutError: If timeout occurs and raise_on_timeout is True
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.error(
            f"Operation '{operation_name}' timed out after {timeout}s",
            extra={'operation': operation_name, 'timeout_seconds': timeout}
        )

        if raise_on_timeout:
            raise
        else:
            logger.warning(
                f"Returning fallback value for '{operation_name}'",
                extra={'operation': operation_name, 'fallback_value': fallback_value}
            )
            return fallback_value


# =============================================================================
# Memory Usage Tracking (for debugging)
# =============================================================================

def log_memory_usage(operation: str = ""):
    """
    Log current memory usage (for debugging).

    Args:
        operation: Operation name for context
    """
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        logger.debug(
            f"Memory usage {f'({operation})' if operation else ''}: "
            f"RSS={mem_info.rss / 1024 / 1024:.1f}MB, "
            f"VMS={mem_info.vms / 1024 / 1024:.1f}MB",
            extra={
                'operation': operation,
                'memory_rss_mb': mem_info.rss / 1024 / 1024,
                'memory_vms_mb': mem_info.vms / 1024 / 1024
            }
        )
    except ImportError:
        logger.debug("psutil not available for memory tracking")
    except Exception as e:
        logger.debug(f"Failed to log memory usage: {e}")
