# Multi-stage production Dockerfile for THULIR Backend
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml /app/backend/
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r /app/backend/pyproject.toml

# Final runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

RUN groupadd -r thulir && useradd -r -g thulir thulir

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY backend /app/backend
COPY scripts /app/scripts

# Set ownership
RUN chown -R thulir:thulir /app

USER thulir

EXPOSE 8000

ENV APP_ENV=production \
    PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

