#!/bin/bash

# Database Seeding Script
# This script seeds the database with initial roles, permissions, and optionally creates a super-admin user.
#
# Usage:
#   ./seed_db.sh                                    # Seed only roles and permissions
#   ./seed_db.sh <username> <email> <password>      # Seed roles, permissions, and create super-admin user
#
# Examples:
#   ./seed_db.sh
#   ./seed_db.sh admin admin@example.com mypassword
#   ./seed_db.sh "John Doe" john@company.com "secure123!"

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

# Function to display usage
show_usage() {
    echo "Usage: $0 [username] [email] [password]"
    echo ""
    echo "Arguments:"
    echo "  username    Username for the super-admin user (optional)"
    echo "  email       Email for the super-admin user (optional)"
    echo "  password    Password for the super-admin user (optional)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Seed only roles and permissions"
    echo "  $0 admin admin@example.com mypassword # Create super-admin user with credentials"
    echo ""
    echo "Note: If any of username, email, or password is provided, all three are required."
}

# Check if help is requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Validate arguments
if [[ $# -gt 0 && $# -lt 3 ]]; then
    echo "Error: If creating a super-admin user, all three arguments (username, email, password) are required."
    echo ""
    show_usage
    exit 1
fi

if [ ! -f "$SEED_SCRIPT" ]; then
  echo "Seed script not found at $SEED_SCRIPT" | tee -a "$LOGFILE"
  exit 1
fi

echo "[INFO] Starting database seeding at $(date)" | tee -a "$LOGFILE"

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR"

# Build command with optional arguments
if [[ $# -eq 3 ]]; then
    echo "[INFO] Creating super-admin user: $1 ($2)" | tee -a "$LOGFILE"
    poetry run python "$SEED_SCRIPT" --username "$1" --email "$2" --password "$3" 2>&1 | tee -a "$LOGFILE"
else
    echo "[INFO] Seeding roles and permissions only" | tee -a "$LOGFILE"
poetry run python "$SEED_SCRIPT" 2>&1 | tee -a "$LOGFILE"
fi

STATUS=${PIPESTATUS[0]}

if [ $STATUS -eq 0 ]; then
  echo "[INFO] Database seeding completed successfully at $(date)" | tee -a "$LOGFILE"
else
  echo "[ERROR] Database seeding failed at $(date)" | tee -a "$LOGFILE"
fi

exit $STATUS 