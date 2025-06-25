@echo off
set PORT=8000
if not "%1"=="" set PORT=%1
poetry run uvicorn app.main:app --host 0.0.0.0 --port %PORT%