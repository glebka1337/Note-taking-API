# import pytest
# from httpx import AsyncClient

# @pytest.mark.asyncio
# class TestNotesRoutes:

#     async def test_create_note(self, async_client: AsyncClient, access_token: str):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         note_data = {"title": "Test Note", "content": "This is a test note", "tag_ids": []}
#         resp = await async_client.post("/notes/", json=note_data, headers=headers)
#         assert resp.status_code == 200
#         note = resp.json()
#         assert note["title"] == note_data["title"]
#         self.note_id = note["id"]

#     async def test_get_notes(self, async_client: AsyncClient, access_token: str):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         resp = await async_client.get("/notes/", headers=headers)
#         assert resp.status_code == 200
        

#     async def test_get_note_by_id(self, async_client: AsyncClient, access_token: str):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         resp = await async_client.get(f"/notes/{self.note_id}", headers=headers)
#         assert resp.status_code == 200
        

#     async def test_update_note(self, async_client: AsyncClient, access_token: str):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         updated_data = {"title": "Updated Note", "content": "Updated content", "tag_ids": []}
#         resp = await async_client.put(f"/notes/{self.note_id}", json=updated_data, headers=headers)
#         assert resp.status_code == 200
#         note = resp.json()
#         assert note["title"] == updated_data["title"]

#     async def test_delete_note(self, async_client: AsyncClient, access_token: str):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         resp = await async_client.delete(f"/notes/{self.note_id}", headers=headers)
#         assert resp.status_code == 200
#         data = resp.json()
#         assert data["ok"] is True