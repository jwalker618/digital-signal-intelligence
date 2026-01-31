# Digital Signal Intelligence - Docker Image
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim

# Labels
LABEL org.opencontainers.image.title="DSI API"
LABEL org.opencontainers.image.description="Digital Signal Intelligence Pricing API"
LABEL org.opencontainers.image.version="0.2.0"
LABEL org.opencontainers.image.vendor="DSI"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    DSI_ENV=production \
    DSI_HOST=0.0.0.0 \
    DSI_PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash dsi && \
    mkdir -p /app /app/.cache && \
    chown -R dsi:dsi /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=dsi:dsi signal_architecture/ ./signal_architecture/
COPY --chown=dsi:dsi infrastructure/ ./infrastructure/
COPY --chown=dsi:dsi layers/ ./layers/
COPY --chown=dsi:dsi coverages/ ./coverages/
COPY --chown=dsi:dsi extractors/ ./extractors/
COPY --chown=dsi:dsi setup.py pyproject.toml README.md ./

# Switch to non-root user
USER dsi

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Run the API
CMD ["uvicorn", "infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
