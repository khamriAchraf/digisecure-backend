#!/bin/bash

# Test Database Seeding Script
# This script seeds the test database with initial data and creates a test super-admin user.
#
# Usage:
#   ./seed_test_db.sh
#
# The script will:
# 1. Load settings from .env.test
# 2. Create all necessary tables in the test schema
# 3. Seed roles and permissions
# 4. Create a test super-admin user with predefined credentials

LOGFILE="seed_test_db.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_SCRIPT="$SCRIPT_DIR/tests/seed_test_db.py"

echo "[INFO] Starting test database seeding at $(date)" | tee -a "$LOGFILE"

# Check if seed script exists
if [ ! -f "$SEED_SCRIPT" ]; then
  echo "Test seed script not found at $SEED_SCRIPT" | tee -a "$LOGFILE"
  exit 1
fi

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR"

# Run the test seeding script
echo "[INFO] Running test database seeding..." | tee -a "$LOGFILE"
poetry run python "$SEED_SCRIPT" 2>&1 | tee -a "$LOGFILE"

STATUS=${PIPESTATUS[0]}

if [ $STATUS -eq 0 ]; then
  echo "[INFO] Test database seeding completed successfully at $(date)" | tee -a "$LOGFILE"
  echo ""
  echo "Test super-admin credentials:"
  echo "  Username: test_admin"
  echo "  Email: test_admin@example.com"
  echo "  Password: test_password_123"
  echo ""
  echo "You can now run your tests with: poetry run pytest"
else
  echo "[ERROR] Test database seeding failed at $(date)" | tee -a "$LOGFILE"
fi

exit $STATUS 