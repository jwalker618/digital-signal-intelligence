# Digital Signal Intelligence - Docker Image
# Multi-stage build for optimised production image

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
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

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    FLASK_ENV=production

# Create non-root user
RUN useradd -m -u 1000 dsi && \
    mkdir -p /app && \
    chown -R dsi:dsi /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=dsi:dsi . .

# Switch to non-root user
USER dsi

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c 'import requests; requests.get("http://localhost:5000/health")' || exit 1

# Run the application with gunicorn
CMD ['gunicorn', '--bind', '0.0.0.0:5000', '--workers', '4', '--timeout', '120', '--access-logfile', '-', '--error-logfile', '-', 'api.server:app']
