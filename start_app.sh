#!/bin/bash
PORT=${1:-8000}
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT 