#!/bin/bash
set -e

echo "[*] Stop and delete all containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || true

echo "[*] Delete previous image..."
docker rmi -f fastapi-docker 2>/dev/null || true

echo "[*] Build image -> fastapi-docker..."
docker build --no-cache -t fastapi-docker .

echo "[*] Run docker-compose for testing..."
docker compose -f docker-compose.test.yml up -d

echo "[*] Waiting for test DB..."
sleep 2
docker exec db_test sh -c "until pg_isready -U test_user -d test_db; do sleep 1; done"
sleep 2

echo "[*] Run tests via AsyncClient script..."
docker exec fastapi_test python /app/tests/test_endpoints.py
TEST_RESULT=$?

echo "[*] Stop test docker-compose..."
docker compose -f docker-compose.test.yml down

if [ $TEST_RESULT -ne 0 ]; then
    echo "[✗] Tests failed! Откатываемся."
    exit 1
else
    echo "[✓] Tests passed! Поднимаем production..."
    docker compose up -d
fi

echo "[✓] Done!"
exit 0