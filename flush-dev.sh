#!/bin/bash

DB_CONTAINER="db_dev"
REDIS_CONTAINER="redis_dev"

echo "Stopping DB and Redis containers..."
sudo docker stop $DB_CONTAINER $REDIS_CONTAINER 2>/dev/null || true

echo "Removing DB and Redis containers..."
sudo docker rm $DB_CONTAINER $REDIS_CONTAINER 2>/dev/null || true

echo "Starting DB and Redis containers..."
sudo docker compose -f docker-compose.dev.yml up -d 

echo "Flush and rebuild complete!"
