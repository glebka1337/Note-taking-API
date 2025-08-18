FROM python:3.12-alpine

WORKDIR /app

COPY ./api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    anyio 
    
COPY ./api /app/api

ENV PYTHONPATH=/app

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
