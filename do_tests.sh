#!/bin/bash

export TESTING=true
export PYTHONPATH=$PWD

DB_PASSWORD="${DB_PASSWORD:-default_password}"
CONTAINER_NAME=postgres-test
IMAGE_NAME="xxx-backend"

docker network rm test-net || true

docker network create test-net

docker rm -f $CONTAINER_NAME 2>/dev/null || true

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



docker run --rm -i --network test-net \
  -e TESTING=true \
  -e DEBUG=true \
  -e ENV=dev \
  -e DB_HOST=postgres-test \
  -e DB_PORT=5433 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=${DB_PASSWORD} \
  -e DB_NAME=dev \
  -e DB_SCHEMA=public \
  -e JWT_SECRET=${JWT_SECRET} \
  -e JWT_ALGORITHM=HS256 \
  -e JWT_EXPIRATION_MINUTES=60 \
  -e JWT_REFRESH_EXPIRATION_DAYS=7 \
  ${IMAGE_NAME}:${version} \
  /bin/bash -c "echo $DB_PASSWORD && echo $DB_PORT && ./run_remote_tests.sh"
