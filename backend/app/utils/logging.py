"""
Structured logging utility for the Building Machinery AI Chatbot backend.

Provides:
- Correlation ID support for distributed tracing
- Consistent log formatting across modules
- Contextual logging with extra fields
- Performance logging helpers
- Sensitive data masking

Usage:
    from app.utils.logging import get_logger, add_correlation_id

    logger = get_logger(__name__)
    logger.info("Processing request", extra={"user_id": "123", "action": "upload"})
"""
import logging
import sys
import json
import time
import uuid
from typing import Dict, Any, Optional
from contextvars import ContextVar
from functools import wraps
import traceback


# Context variable for correlation ID (thread-safe for async)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


# =============================================================================
# Correlation ID Management
# =============================================================================

def generate_correlation_id() -> str:
    """
    Generate a new correlation ID for request tracking.

    Returns:
        UUID string for correlation
    """
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.

    Args:
        correlation_id: Optional correlation ID. If None, generates new one.

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id_var.set(None)


# =============================================================================
# Structured Log Formatter
# =============================================================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with correlation ID support.

    Outputs logs as JSON with consistent structure:
    - timestamp
    - level
    - logger name
    - message
    - correlation_id (if present)
    - extra fields
    - exception info (if present)
    """

    # Fields to mask in logs (security)
    SENSITIVE_FIELDS = {
        'password', 'password_hash', 'token', 'secret', 'api_key',
        'access_token', 'refresh_token', 'authorization'
    }

    def __init__(self, include_correlation_id: bool = True):
        """
        Initialize formatter.

        Args:
            include_correlation_id: Whether to include correlation ID in output
        """
        super().__init__()
        self.include_correlation_id = include_correlation_id

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        # Base log data
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add correlation ID if available and enabled
        if self.include_correlation_id:
            correlation_id = get_correlation_id()
            if correlation_id:
                log_data['correlation_id'] = correlation_id

        # Add extra fields (from extra parameter)
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                # Skip standard logging fields
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'message', 'pathname', 'process', 'processName',
                    'relativeCreated', 'thread', 'threadName', 'exc_info',
                    'exc_text', 'stack_info', 'correlation_id'
                ]:
                    # Mask sensitive fields
                    if key.lower() in self.SENSITIVE_FIELDS:
                        log_data[key] = '***MASKED***'
                    else:
                        log_data[key] = self._serialize_value(value)

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }

        # Add file location info
        log_data['location'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }

        return json.dumps(log_data, default=str)

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize value for JSON output.

        Args:
            value: Value to serialize

        Returns:
            JSON-serializable value
        """
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)


# =============================================================================
# Simplified Text Formatter for Development
# =============================================================================

class SimpleTextFormatter(logging.Formatter):
    """
    Human-readable formatter for development/console output.

    Format: [TIMESTAMP] [LEVEL] [LOGGER] [CORRELATION_ID] MESSAGE
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def __init__(self, use_colors: bool = True, include_correlation_id: bool = True):
        """
        Initialize formatter.

        Args:
            use_colors: Whether to use ANSI colors
            include_correlation_id: Whether to include correlation ID
        """
        super().__init__()
        self.use_colors = use_colors
        self.include_correlation_id = include_correlation_id

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        # Color setup
        color = self.COLORS.get(record.levelname, '') if self.use_colors else ''
        reset = self.COLORS['RESET'] if self.use_colors else ''

        # Build message parts
        parts = [
            f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}]",
            f"{color}[{record.levelname}]{reset}",
            f"[{record.name}]"
        ]

        # Add correlation ID if present
        if self.include_correlation_id:
            correlation_id = get_correlation_id()
            if correlation_id:
                parts.append(f"[{correlation_id[:8]}]")  # Show first 8 chars

        # Add message
        parts.append(record.getMessage())

        message = ' '.join(parts)

        # Add exception if present
        if record.exc_info:
            message += '\n' + ''.join(traceback.format_exception(*record.exc_info))

        return message


# =============================================================================
# Logger Factory
# =============================================================================

def get_logger(
    name: str,
    level: Optional[str] = None,
    structured: bool = True
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level if provided
    if level:
        logger.setLevel(getattr(logging, level.upper()))

    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        # Choose formatter based on structured flag
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = SimpleTextFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# =============================================================================
# Performance Logging Decorator
# =============================================================================

def log_performance(
    logger: Optional[logging.Logger] = None,
    level: str = 'INFO',
    include_args: bool = False
):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance (if None, creates one from function module)
        level: Log level for performance message
        include_args: Whether to include function arguments in log

    Usage:
        @log_performance()
        def slow_function():
            time.sleep(1)
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            extra = {'function': func_name}
            if include_args:
                extra['args'] = str(args)[:100]  # Limit length
                extra['kwargs'] = str(kwargs)[:100]

            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                getattr(logger, level.lower())(
                    f"Function '{func_name}' completed in {elapsed:.3f}s",
                    extra={**extra, 'duration_seconds': elapsed, 'status': 'success'}
                )

                return result
            except Exception as e:
                elapsed = time.time() - start_time

                logger.error(
                    f"Function '{func_name}' failed after {elapsed:.3f}s: {str(e)}",
                    extra={**extra, 'duration_seconds': elapsed, 'status': 'error'},
                    exc_info=True
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            extra = {'function': func_name}
            if include_args:
                extra['args'] = str(args)[:100]
                extra['kwargs'] = str(kwargs)[:100]

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                getattr(logger, level.lower())(
                    f"Function '{func_name}' completed in {elapsed:.3f}s",
                    extra={**extra, 'duration_seconds': elapsed, 'status': 'success'}
                )

                return result
            except Exception as e:
                elapsed = time.time() - start_time

                logger.error(
                    f"Function '{func_name}' failed after {elapsed:.3f}s: {str(e)}",
                    extra={**extra, 'duration_seconds': elapsed, 'status': 'error'},
                    exc_info=True
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# Contextual Logging Helper
# =============================================================================

class LogContext:
    """
    Context manager for adding consistent extra fields to logs.

    Usage:
        with LogContext(user_id="123", action="upload"):
            logger.info("Processing")  # Will include user_id and action
    """

    def __init__(self, **kwargs):
        """
        Initialize context with extra fields.

        Args:
            **kwargs: Extra fields to add to all logs in this context
        """
        self.extra = kwargs
        self.old_factory = None

    def __enter__(self):
        """Enter context and modify log record factory."""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original factory."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# =============================================================================
# Request Logging Helpers
# =============================================================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user_id: Optional[str] = None,
    **extra
):
    """
    Log an incoming HTTP request.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        user_id: User ID if authenticated
        **extra: Additional fields
    """
    log_data = {
        'event_type': 'http_request',
        'method': method,
        'path': path,
    }

    if user_id:
        log_data['user_id'] = user_id

    log_data.update(extra)

    logger.info(f"{method} {path}", extra=log_data)


def log_response(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
    **extra
):
    """
    Log an HTTP response.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_seconds: Request duration
        **extra: Additional fields
    """
    log_data = {
        'event_type': 'http_response',
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration_seconds': duration_seconds,
    }

    log_data.update(extra)

    level = 'error' if status_code >= 500 else 'warning' if status_code >= 400 else 'info'

    getattr(logger, level)(
        f"{method} {path} - {status_code} ({duration_seconds:.3f}s)",
        extra=log_data
    )
