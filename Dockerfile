FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-ansi --no-root

COPY . .

RUN chmod +x run_all_tests.sh run_unit_tests.sh run_e2e_tests.sh do_tests.sh || true

EXPOSE 8000

CMD ["bash", "-c", "./seed_db.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]