# =============================================================================
# Production Dockerfile for Baumaschinen-KI Frontend (React + Vite)
# =============================================================================
# Multi-stage build: Node.js for building, Nginx for serving
# Optimized for Vite + React production deployment
# Security: Non-root user, minimal image, health checks
# =============================================================================

# ============================================================================
# Stage 1: Build Stage (Node.js)
# ============================================================================
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files first (for layer caching)
COPY package*.json ./

# Install dependencies (including devDependencies for building)
RUN npm ci && \
    npm cache clean --force

# Copy application source
COPY . .

# Build arguments for environment variables (Vite uses VITE_ prefix)
ARG VITE_API_URL
ARG VITE_APP_NAME=Baumaschinen-KI
ARG VITE_ENVIRONMENT=production
ARG BUILD_VERSION
ARG BUILD_DATE
ARG VCS_REF

# Set environment variables for build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
ENV VITE_ENVIRONMENT=${VITE_ENVIRONMENT}
ENV NODE_ENV=production

# Build the application (Vite outputs to /dist)
RUN npm run build

# Verify build output exists
RUN ls -la /app/dist && test -f /app/dist/index.html || (echo "Build failed - no index.html found" && exit 1)

# ============================================================================
# Stage 2: Production Stage (Nginx)
# ============================================================================
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default Nginx configuration
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom Nginx configuration for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage (Vite outputs to dist/)
COPY --from=builder /app/dist /usr/share/nginx/html

# Create necessary directories and set permissions
# Note: nginx:alpine runs as nginx user by default (UID 101)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check - verify Nginx is serving content
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Add metadata labels
LABEL org.opencontainers.image.title="Baumaschinen-KI Frontend" \
      org.opencontainers.image.description="React + Vite frontend with Nginx" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Rueko GmbH"

# Start Nginx (runs as nginx user by default)
CMD ["nginx", "-g", "daemon off;"]
