#!/bin/sh

pip install -r /app/api/requirements.txt --no-cache-dir

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload