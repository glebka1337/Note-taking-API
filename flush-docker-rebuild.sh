#!/bin/bash
set -e

echo "[*] Stop and delete all containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || true

echo "[*] Delete previous images..."
docker rmi -f fastapi-docker fastapi_test 2>/dev/null || true

echo "[*] Build image -> fastapi-docker..."
docker build --no-cache -t fastapi-docker .

echo "[*] Run docker-compose for testing (with forced rebuild)..."
docker compose -f docker-compose.test.yml up -d --build --force-recreate

echo "[*] Waiting for test DB..."
sleep 2
until docker exec db_test pg_isready -U test_user -d test_db; do
  echo "[*] Waiting for PostgreSQL to be ready..."
  sleep 1
done
sleep 2

echo "[*] Running tests with pytest..."
docker exec fastapi_test pytest -v
TEST_RESULT=$?

echo "[*] Stop test environment..."
docker compose -f docker-compose.test.yml down

if [ $TEST_RESULT -ne 0 ]; then
    echo "[✗] Tests failed! No deployment."
    exit 1
else
    echo "[✓] Tests passed! Deploying production..."
    docker compose up -d
fi

echo "[✓] Done!"