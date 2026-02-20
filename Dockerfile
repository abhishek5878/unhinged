FROM python:3.11-slim

WORKDIR /app

# System deps for pgvector, sentence-transformers, psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -e .

# Copy source
COPY apriori/ apriori/
COPY alembic/ alembic/
COPY alembic.ini .

# Run migrations then start server
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn apriori.api.main:app --host 0.0.0.0 --port 8000"]
