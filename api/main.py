from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager
from api.core.db import Base, async_engine
from api.notes.router import router as notes_router
from api.tags.router import router as tags_router
import time
import logging
from api.auth.router import router as auth_router

logger = logging.getLogger("docker_api")
logger.setLevel(logging.INFO)

if logger.handlers:
    logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler("api.log", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created or already exist.")
    yield

app = FastAPI(
    title="Docker API",
    version="1.0.0",
    lifespan=lifespan,
    debug=True
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


@app.post('/flush-db', status_code=status.HTTP_200_OK)
async def flush_db():
    """
    WARNING: This endpoint will drop and recreate all database tables.
    Use with caution, primarily for testing or development purposes.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables dropped and recreated.")
    return {"status": "Database flushed and reset."}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url} - {str(e)}", exc_info=True)
        raise

    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url} "
        f"Status: {response.status_code} Process time: {process_time:.4f}s"
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(auth_router)