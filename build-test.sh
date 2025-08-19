#!/bin/sh

set -e

echo "Stopping and removing old running test containers..."

docker container stop db_test fastapi_test redis_test
docker container rm db_test fastapi_test redis_test

echo "Removing old images..."
docker image rm fastapidocker-fastapi_test:latest  

echo "Building new image..."
docker build --no-cache -t fastapidocker-fastapi_test:latest .

echo "Starting test environment..."
docker compose -f docker-compose.test.yml up -d

echo "Waiting for test DB..."
sleep 2
until docker exec db_test pg_isready -U test_user -d test_db; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 1
done
sleep 2

echo "Running tests with pytest..."
docker exec fastapi_test pytest -v
TEST_RESULT=$?

echo "Stopping test environment..."
docker compose -f docker-compose.test.yml down

exit $TEST_RESULT
