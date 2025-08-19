import pytest
from httpx import AsyncClient

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_create_and_get_tag():
    async with AsyncClient(base_url=BASE_URL) as client:
        
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "Password123"
        }
        resp = await client.post("/auth/register", json=user_data)
        assert resp.status_code == 200
        user = resp.json()
        user_id = user["id"]

        # Теперь создаём тег
        tag_data = {"name": "test_tag", "user_id": user_id}
        response = await client.post("/tags/", json=tag_data)
        assert response.status_code == 200
        tag = response.json()
        assert tag["name"] == "test_tag"

        # Проверяем получение тегов
        response = await client.get("/tags/")
        assert response.status_code == 200
        tags = response.json()
        assert any(t["name"] == "test_tag" for t in tags)


@pytest.mark.asyncio
async def test_create_and_get_note():
    async with AsyncClient(base_url=BASE_URL) as client:
        # Создаём юзера
        user_data = {
            "username": "noteuser",
            "email": "noteuser@example.com",
            "password": "Password123"
        }
        resp = await client.post("/auth/register", json=user_data)
        assert resp.status_code == 200
        user = resp.json()
        user_id = user["id"]

        # Создаём заметку
        note_data = {
            "title": "note1",
            "content": "some content",
            "tag_ids": [],
            "user_id": user_id
        }
        response = await client.post("/notes/", json=note_data)
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "note1"

        # Читаем заметку обратно
        note_id = note["id"]
        response = await client.get(f"/notes/{note_id}")
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "note1"
