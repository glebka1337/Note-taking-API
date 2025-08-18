from httpx import AsyncClient

async def test_create_and_get_tag(async_client):
    # создаём тег
    tag_data = {"name": "test_tag"}
    response = await async_client.post("/tags/", json=tag_data)
    assert response.status_code == 200
    tag = response.json()
    assert tag["name"] == "test_tag"

    # получаем список тегов
    response = await async_client.get("/tags/")
    assert response.status_code == 200
    tags = response.json()
    assert any(t["name"] == "test_tag" for t in tags)


async def test_create_and_get_note(async_client):
    # создаём заметку
    note_data = {"title": "note1", "content": "some content", "tag_ids": []}
    response = await async_client.post("/notes/", json=note_data)
    assert response.status_code == 200
    note = response.json()
    assert note["title"] == "note1"

    # получаем заметку
    note_id = note["id"]
    response = await async_client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    note = response.json()
    assert note["title"] == "note1"

async def main():
    async with AsyncClient(base_url="http://localhost:8000") as async_client:
        await test_create_and_get_tag(async_client)
        await test_create_and_get_note(async_client)
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())