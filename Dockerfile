# CONCEPT: Multi-stage Docker Build
# =====================================
# Stage 1 (builder): installs dependencies
# Stage 2 (runtime): copies only what's needed — smaller final image

FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies before copying source (Docker layer cache:
# if requirements.txt unchanged, this layer is reused on rebuild)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create non-root user for security
RUN useradd -r -s /bin/false appuser && chown -R appuser /app
USER appuser

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

# CONCEPT: Health check
# Docker restarts the container if health check fails N times
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# --workers 4: number of Uvicorn worker processes (use for production)
# For async apps, workers=1 is often fine; use Gunicorn for multi-worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
