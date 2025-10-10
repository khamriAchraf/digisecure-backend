#!/bin/bash

export TESTING=true

DB_PASSWORD="${DB_PASSWORD:-default_password}"
CONTAINER_NAME=postgres-test
IMAGE_NAME="xxx-backend"

docker network create test-net

docker run -p 5433:5432 --name postgres-test --network test-net -e POSTGRES_PASSWORD=$DB_PASSWORD -d postgres:17

echo "Waiting for Postgres to start..."
until docker exec $CONTAINER_NAME pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

echo "Creating databases ..."
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME \
  psql -U postgres -c "CREATE DATABASE dev;"

docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME \
  psql -U postgres -c "CREATE DATABASE test;"

echo "Database 'dev', 'test' created successfully."

source ./version.sh
echo "Building version: $version"

PROJECT_ROOT="$(dirname "$0")/.."
cd "$PROJECT_ROOT"

docker build -t ${IMAGE_NAME}:${version} -t ${IMAGE_NAME}:latest .

docker rm -f ${IMAGE_NAME}-test || true

echo ''
echo '  /$$$$$$              /$$                                         /$$                     /$$       /$$$$$$$$                    /$$             '
echo ' /$$__  $$            | $$                                        | $$                    | $$      |__  $$__/                   | $$             '
echo '| $$  \ $$ /$$   /$$ /$$$$$$    /$$$$$$  /$$$$$$/$$$$   /$$$$$$  /$$$$$$    /$$$$$$   /$$$$$$$         | $$  /$$$$$$   /$$$$$$$ /$$$$$$   /$$$$$$$'
echo '| $$$$$$$$| $$  | $$|_  $$_/   /$$__  $$| $$_  $$_  $$ |____  $$|_  $$_/   /$$__  $$ /$$__  $$         | $$ /$$__  $$ /$$_____/|_  $$_/  /$$_____/'
echo '| $$__  $$| $$  | $$  | $$    | $$  \ $$| $$ \ $$ \ $$  /$$$$$$$  | $$    | $$$$$$$$| $$  | $$         | $$| $$$$$$$$|  $$$$$$   | $$   |  $$$$$$ '
echo '| $$  | $$| $$  | $$  | $$ /$$| $$  | $$| $$ | $$ | $$ /$$__  $$  | $$ /$$| $$_____/| $$  | $$         | $$| $$_____/ \____  $$  | $$ /$$\____  $$'
echo '| $$  | $$|  $$$$$$/  |  $$$$/|  $$$$$$/| $$ | $$ | $$|  $$$$$$$  |  $$$$/|  $$$$$$$|  $$$$$$$         | $$|  $$$$$$$ /$$$$$$$/  |  $$$$//$$$$$$$/'
echo '|__/  |__/ \______/    \___/   \______/ |__/ |__/ |__/ \_______/   \___/   \_______/ \_______/         |__/ \_______/|_______/    \___/ |_______/ '
echo '                                                                                                                                                  '
echo '                                                                                                                                                  '
echo '                                                                                                                                                  '



docker run --rm -it --network test-net \
  -e ENV=dev \
  ${IMAGE_NAME}:${version} \
  /bin/bash -c "export TESTING=true && ./run_all_tests.sh"