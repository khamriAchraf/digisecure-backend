FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# System deps (add dev headers only if needed by your deps)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-ansi --no-root

# Copy application code
COPY . .

EXPOSE 8000

# Default command starts FastAPI app; docker-compose overrides to run seeding first
CMD /bin/bash -c "./seed_db.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"