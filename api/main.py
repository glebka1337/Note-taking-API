from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from api.db import Base, async_engine
from api.notes.router import router as notes_router
from api.tags.router import router as tags_router
import time
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Simple logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log the incoming request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the response
    logger.info(
        f"Response: {request.method} {request.url} "
        f"Status: {response.status_code} "
        f"Process time: {process_time:.4f}s"
    )
    
    # You could also add the process time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

app.include_router(notes_router)
app.include_router(tags_router)