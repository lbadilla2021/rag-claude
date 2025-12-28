FROM python:3.11-slim

LABEL maintainer="Luciano - Apex 360"
LABEL description="Apex AI - Backend RAG Enterprise (Postgres + Qdrant)"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN useradd -m appuser

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar backend
COPY backend.py .
COPY app ./app

# Directorios persistentes
RUN mkdir -p /app/uploads /app/logs && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
