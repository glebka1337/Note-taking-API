from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from api.core.db import Base, async_engine
from api.notes.router import router as notes_router
from api.tags.router import router as tags_router
import time
import logging
from api.auth.router import router as auth_router

# --- Настройка логгера с записью в файл и в консоль ---
logger = logging.getLogger("docker_api")
logger.setLevel(logging.INFO)

# Убираем обработчики, если они уже есть (чтобы не дублировать)
if logger.handlers:
    logger.handlers.clear()

# Формат
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler для файла
file_handler = logging.FileHandler("api.log", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Handler для консоли (опционально, можно убрать, если не нужен вывод в терминал)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Добавляем обработчики
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- Остальной код ---
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