#!/bin/bash

# Database Seeding Script
# This script seeds the database with initial roles, permissions, and always creates a default super-admin user (admin/admin@admin.com/admin).
#
# Usage:
#   ./seed_db.sh [--load-test]
#
# The script will always create the default admin user. Use --load-test to generate random users for load testing.

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

LOGFILE="seed_db.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_SCRIPT="$SCRIPT_DIR/app/utils/seed_db_schema.py"
LOAD_TEST_SCRIPT="$SCRIPT_DIR/app/utils/generate_load_test_users.py"

if [ ! -f "$SEED_SCRIPT" ]; then
  echo "Seed script not found at $SEED_SCRIPT" | tee -a "$LOGFILE"
  exit 1
fi

# Check for --load-test flag
if [[ "$1" == "--load-test" ]]; then
  echo "[INFO] Running normal seeding before load test user generation..." | tee -a "$LOGFILE"
  export PYTHONPATH="$SCRIPT_DIR"
  poetry run python "$SEED_SCRIPT" --username admin --email admin@admin.com --password admin 2>&1 | tee -a "$LOGFILE"
  STATUS=${PIPESTATUS[0]}
  if [ $STATUS -ne 0 ]; then
    echo "[ERROR] Database seeding failed, aborting load test user generation." | tee -a "$LOGFILE"
    exit $STATUS
  fi
  if [ ! -f "$LOAD_TEST_SCRIPT" ]; then
    echo "Load test user generation script not found at $LOAD_TEST_SCRIPT" | tee -a "$LOGFILE"
    exit 1
  fi
  echo "[INFO] Generating random users for load testing..." | tee -a "$LOGFILE"
  poetry run python "$LOAD_TEST_SCRIPT" 2>&1 | tee -a "$LOGFILE"
  STATUS=${PIPESTATUS[0]}
  if [ $STATUS -eq 0 ]; then
    echo "[INFO] Load test user generation completed successfully at $(date)" | tee -a "$LOGFILE"
  else
    echo "[ERROR] Load test user generation failed at $(date)" | tee -a "$LOGFILE"
  fi
  exit $STATUS
fi

echo "[INFO] Starting database seeding at $(date)" | tee -a "$LOGFILE"

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR"

echo "[INFO] Seeding roles, permissions, and creating default admin user (admin/admin@admin.com/admin)" | tee -a "$LOGFILE"
poetry run python "$SEED_SCRIPT" --username admin --email admin@admin.com --password admin 2>&1 | tee -a "$LOGFILE"

STATUS=${PIPESTATUS[0]}

if [ $STATUS -eq 0 ]; then
  echo "[INFO] Database seeding completed successfully at $(date)" | tee -a "$LOGFILE"
else
  echo "[ERROR] Database seeding failed at $(date)" | tee -a "$LOGFILE"
fi

exit $STATUS 