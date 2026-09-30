#!/bin/bash
PORT=${1:-8000}
export PYTHONPATH=$PWD
python dags/
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT