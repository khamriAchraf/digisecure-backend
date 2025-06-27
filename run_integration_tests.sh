#!/bin/bash
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

export PYTHONPATH=$PWD
export TESTING=true

echo '                                                                                                                                                                       '
echo '                                                                                                                                                                       '
echo '                                                                                                                                                                       '
echo '    /$$$$$$ /$$   /$$ /$$$$$$$$ /$$$$$$$$  /$$$$$$  /$$$$$$$   /$$$$$$  /$$$$$$$$ /$$$$$$  /$$$$$$  /$$   /$$       /$$$$$$$$ /$$$$$$$$  /$$$$$$  /$$$$$$$$ /$$$$$$    '
echo '   |_  $$_/| $$$ | $$|__  $$__/| $$_____/ /$$__  $$| $$__  $$ /$$__  $$|__  $$__/|_  $$_/ /$$__  $$| $$$ | $$      |__  $$__/| $$_____/ /$$__  $$|__  $$__//$$__  $$   '
echo '     | $$  | $$$$| $$   | $$   | $$      | $$  \__/| $$  \ $$| $$  \ $$   | $$     | $$  | $$  \ $$| $$$$| $$         | $$   | $$      | $$  \__/   | $$  | $$  \__/   '
echo '     | $$  | $$ $$ $$   | $$   | $$$$$   | $$ /$$$$| $$$$$$$/| $$$$$$$$   | $$     | $$  | $$  | $$| $$ $$ $$         | $$   | $$$$$   |  $$$$$$    | $$  |  $$$$$$    '
echo '     | $$  | $$  $$$$   | $$   | $$__/   | $$|_  $$| $$__  $$| $$__  $$   | $$     | $$  | $$  | $$| $$  $$$$         | $$   | $$__/    \____  $$   | $$   \____  $$   '
echo '     | $$  | $$\  $$$   | $$   | $$      | $$  \ $$| $$  \ $$| $$  | $$   | $$     | $$  | $$  | $$| $$\  $$$         | $$   | $$       /$$  \ $$   | $$   /$$  \ $$   '
echo '    /$$$$$$| $$ \  $$   | $$   | $$$$$$$$|  $$$$$$/| $$  | $$| $$  | $$   | $$    /$$$$$$|  $$$$$$/| $$ \  $$         | $$   | $$$$$$$$|  $$$$$$/   | $$  |  $$$$$$/   '
echo '   |______/|__/  \__/   |__/   |________/ \______/ |__/  |__/|__/  |__/   |__/   |______/ \______/ |__/  \__/         |__/   |________/ \______/    |__/   \______/    '
echo '                                                                                                                                                                       '                                                                                                                                                                 
echo '                                                                                                                                                                       '                                                                                                                                                                 
echo '                                                                                                                                                                       '                                                                                                                                                                 

echo "Cleaning test schema..."
poetry run python app/utils/clean_db_schema.py

echo "Seeding database..."
poetry run python app/utils/seed_db_schema.py --username admin --email admin@admin.com --password admin

echo "Running integration tests only..."
poetry run pytest -m integration --tb=short 