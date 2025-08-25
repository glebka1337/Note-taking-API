from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager
from api.core.db import Base, async_engine
from api.notes.router import router as notes_router
from api.tags.router import router as tags_router
from api.auth.router import router as auth_router
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
    return {"status": "Database flushed and reset."}

app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(auth_router)
