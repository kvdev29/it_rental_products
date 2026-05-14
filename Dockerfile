# Dockerfile
# ─────────────────────────────────────────────────────────────────────────
# Multi-stage build for SecureITSM Flask application
#
# Stage 1 (builder) – installs Python dependencies into a virtual env
# Stage 2 (runtime) – copies only the venv and app code (smaller image)
#
# Security practices applied:
#   - Non-root user (principle of least privilege)
#   - No secrets in the image (passed as env vars at runtime)
#   - Minimal base image (python:3.12-slim)
#   - .dockerignore prevents sensitive files being included
#
# Usage:
#   docker build -t secureit-itsm .
#   docker run -p 5000:5000 --env-file .env secureit-itsm
# ─────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────── #
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (cached layer if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────── #
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security (principle of least privilege)
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/auth/login')" || exit 1

# Run the application
# In production, use gunicorn instead of the Flask dev server
CMD ["python", "run.py"]
