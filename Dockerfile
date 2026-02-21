FROM python:3.11-slim

WORKDIR /app

# System deps for pgvector, psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all source first (hatchling needs the package dir to build the wheel)
COPY pyproject.toml .
COPY apriori/ apriori/
COPY alembic/ alembic/
COPY alembic.ini .

# Install package + dependencies
RUN pip install --no-cache-dir -e .

# Run migrations then start server
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["sh", "-c", "echo '[startup] running alembic...' && (alembic upgrade head 2>&1 || echo '[startup] alembic migration failed, continuing anyway...') && echo '[startup] starting uvicorn on port ${PORT:-8000}...' && uvicorn apriori.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
