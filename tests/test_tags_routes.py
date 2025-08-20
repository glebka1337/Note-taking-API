import uuid
import pytest
from httpx import AsyncClient
import pytest_asyncio

@pytest_asyncio.fixture
async def created_tag_id(
    async_client: AsyncClient,
    access_token: str
):

    tag_data = {"name": "test_tag:{}".format(str(uuid.uuid4())[:8])}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await async_client.post("/tags/", json=tag_data, headers=headers)
    print(response.json(), "response.status_code: ", response.status_code)
    return response.json()["id"]


@pytest.mark.asyncio
class TestTagsRoutes:

    async def test_create_tag(self, async_client: AsyncClient, access_token: str):
        tag_data = {"name": "test_tag:{}".format(str(uuid.uuid4())[:8])}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.post("/tags/", json=tag_data, headers=headers)
        print(response.json(), "response.status_code: ", response.status_code)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == tag_data["name"]

    async def test_get_tags(self, async_client: AsyncClient, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get("/tags/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    async def test_get_tag(
        self,
        async_client: AsyncClient,
        access_token: str,
        created_tag_id: str,
    ):
    
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get(f"/tags/{created_tag_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_tag_id
        assert "name" in data
        
    async def test_update_tag(
        self,
        async_client: AsyncClient,
        access_token: str,
        created_tag_id: str,
    ):
        updated_data = {"name": "updated_tag_name"}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.put(
            f"/tags/{created_tag_id}", json=updated_data, headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_tag_id
        assert data["name"] == updated_data["name"]
        
    async def test_delete_tag(
        self,
        async_client: AsyncClient,
        access_token: str,
        created_tag_id: str,
    ):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.delete(f"/tags/{created_tag_id}", headers=headers)
        assert response.status_code == 200
    
    
