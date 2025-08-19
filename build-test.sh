#!/bin/sh

set -e

echo "Check if test containers are running..."

if docker container inspect db_test fastapi_test redis_test > /dev/null 2>&1; then
    echo "Test containers are already running. Stopping and removing them..."
    docker container stop db_test fastapi_test redis_test
    docker container rm db_test fastapi_test redis_test
else
    echo "No test containers found. Proceeding to build and start new ones..."
fi

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
