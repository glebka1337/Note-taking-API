import pytest
from httpx import AsyncClient
import pytest_asyncio

@pytest.mark.asyncio
async def test_create_and_get_tag():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        
        tag_data = {"name": "test_tag"}
        response = await client.post("/tags/", json=tag_data)
        assert response.status_code == 200
        tag = response.json()
        assert tag["name"] == "test_tag"

        response = await client.get("/tags/")
        assert response.status_code == 200
        tags = response.json()
        assert any(t["name"] == "test_tag" for t in tags)


@pytest.mark.asyncio
async def test_create_and_get_note():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        
        note_data = {"title": "note1", "content": "some content", "tag_ids": []}
        response = await client.post("/notes/", json=note_data)
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "note1"

        note_id = note["id"]
        response = await client.get(f"/notes/{note_id}")
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "note1"