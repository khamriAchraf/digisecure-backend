# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy only requirements to cache dependencies
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry install --no-root --only main

# Copy project files
COPY . /app

# Expose the port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/bin/bash", "start_app.sh"] 