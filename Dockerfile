# Digital Signal Intelligence - Docker Image
# Multi-stage build for optimized production image
#
# Note: API functionality is being reimplemented.
# This Dockerfile is a placeholder for future API deployment.

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN useradd -m -u 1000 dsi && \
    mkdir -p /app && \
    chown -R dsi:dsi /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=dsi:dsi . .

USER dsi

# Default command - can be overridden for specific use cases
CMD ["python", "-c", "print('DSI container ready. API implementation pending.')"]
