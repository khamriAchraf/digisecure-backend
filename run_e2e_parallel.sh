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

echo '                                                                                                 '
echo '                                                                                                 '
echo '                  /$$$$$$                  /$$$$$$$$ /$$$$$$$$  /$$$$$$  /$$$$$$$$ /$$$$$$       '
echo '                 /$$__  $$                |__  $$__/| $$_____/ /$$__  $$|__  $$__//$$__  $$      '
echo '        /$$$$$$ |__/  \ $$  /$$$$$$          | $$   | $$      | $$  \__/   | $$  | $$  \__/      '
echo '       /$$__  $$  /$$$$$$/ /$$__  $$         | $$   | $$$$$   |  $$$$$$    | $$  |  $$$$$$       '
echo '      | $$$$$$$$ /$$____/ | $$$$$$$$         | $$   | $$__/    \____  $$   | $$   \____  $$      '
echo '      | $$_____/| $$      | $$_____/         | $$   | $$       /$$  \ $$   | $$   /$$  \ $$      '
echo '      |  $$$$$$$| $$$$$$$$|  $$$$$$$         | $$   | $$$$$$$$|  $$$$$$/   | $$  |  $$$$$$/      '
echo '       \_______/|________/ \_______/         |__/   |________/ \______/    |__/   \______/       '
echo '                                                                                                 '
echo '                                                                                                 '                                                                                     
                                                                                     
                                                                                     

echo "Cleaning test schema..."
poetry run python app/utils/clean_db_schema.py

echo "Seeding database..."
poetry run python app/utils/seed_db_schema.py --username admin --email admin@admin.com --password admin

echo "Running e2e tests only..."
poetry run pytest -n 2 -m e2e --tb=short 