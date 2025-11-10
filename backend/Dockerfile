# =============================================================================
# Production Dockerfile for Baumaschinen-KI Backend (FastAPI)
# =============================================================================
# Multi-stage build for optimized production image
# Base: Python 3.12 slim for minimal attack surface
# Security: Non-root user, minimal packages, health checks
# =============================================================================

# Stage 1: Build stage
FROM python:3.12-slim AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
# 1. Run the default install script
# 2. In the same command, move the 'uv' binary to a standard PATH location
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock* ./

# Create a virtual environment
# This will now work because 'uv' is in /usr/local/bin
RUN uv venv .venv

# Install dependencies into the virtual environment
# We tell uv to use the venv's python and it will find uv.lock
RUN uv pip sync --no-cache --python .venv/bin/python pyproject.toml


# Stage 2: Production runtime stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Define the venv path
    VENV_PATH=/app/.venv \
    # Add the venv's bin to the PATH. This is the correct way.
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with home directory
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv ${VENV_PATH}

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure appuser owns the venv
RUN chown -R appuser:appuser ${VENV_PATH}

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check - verify FastAPI is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with uvicorn
# This works because uvicorn is on the PATH (from the venv)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]