from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient
from api.core.db import async_session, async_engine
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(base_url="http://localhost:8000", timeout=1000) as client:
        yield client

async def drop_dev_db(async_client: AsyncClient):
    response = await async_client.post("/flush-db")
    print("✅ Development database dropped and recreated. Ready for tests.")

@pytest_asyncio.fixture(scope="function", autouse=True)
async def flush_dev_db(async_client: AsyncClient):
    await drop_dev_db(async_client)
    
@pytest_asyncio.fixture
async def db_connection() -> AsyncGenerator[AsyncSession, None]:
    async with async_engine.begin() as conn:
        async with async_session(bind=conn) as session:
            yield session

async def _access_token(async_client: AsyncClient) -> str:
    """
    Create a user and return an access token for that user after logging in.
    This function can be used in tests to authenticate requests.
    """

    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123"
    }

    await async_client.post("/auth/register", json=user_data)


    resp = await async_client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    return resp.json()["access_token"]

@pytest_asyncio.fixture
async def access_token(async_client: AsyncClient) -> str:
    return await _access_token(async_client)
