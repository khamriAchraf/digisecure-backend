#!/bin/bash
PORT=${1:-8000}
export PYTHONPATH=$PWD
unset DB_HOST
unset DB_PORT
unset DB_NAME
unset DB_USER
unset DB_SCHEMA
unset DB_PASSWORD
unset JWT_SECRET
unset JWT_ALGORITHM
unset JWT_EXPIRATION_MINUTES
unset JWT_REFRESH_EXPIRATION_DAYS
unset TESTING

poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload