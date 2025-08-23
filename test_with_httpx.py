import httpx
import asyncio
from pprint import pprint as pp

async def drop_dev_db(async_client: httpx.AsyncClient):
    response = await async_client.post("/flush-db")
    assert response.status_code == 200
    print("✅ Development database dropped and recreated. Ready for tests.")

async def auth_test_user(
    async_client: httpx.AsyncClient,
    auth_data: dict
) -> str:
    await async_client.post(
        "/auth/register", json=auth_data
    )
    # If user already exists, try to login
    result_of_login = await async_client.post(
        "/auth/login", json={
            "password": auth_data["password"],
            "email": auth_data["email"]
        }
    )
    
    return result_of_login.json()["access_token"]

    

async def test_create_note_with_relations():
    
    # create client 
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=1000) as client:
        
        # flush db before any tests
        await drop_dev_db(client)
        
        # get token for auth 
        token = await auth_test_user(
            client,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongPass123!#"
            }
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Создаем несколько заметок для ссылок
        notes_for_links = []
        for i in range(2):
            note_data = {
                "title": f"Target Note {i}",
                "content": f"Content for target note {i}",
                "parent_id": None
            }
            response = await client.post("/notes/", json=note_data, headers=headers)
            print(
                'Created note with UUID: {}'.format(response.json()['uuid'])
            )
            notes_for_links.append(response.json())
        
        # 5. Создаем основную заметку с детьми, тегами и ссылками
        main_note_content = f"""
        This is a test note with relations
        
        Test tags:
        #important
        #test
        
        Test children:
        [[First Child Note]]
        [[Second Child Note]]
        
        Test cross links:
        [test-link1]({notes_for_links[0]['uuid']})
        [test-link2]({notes_for_links[1]['uuid']})          
        """
        
        main_note_data = {
            "title": "Main Test Note",
            "content": main_note_content,
            "parent_id": None
        }
        
        response = await client.post("/notes/", json=main_note_data, headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # # check serever response (tags)
        # assert result["title"] == "Main Test Note"
        # assert "important" in [tag["name"] for tag in result["tags_read"]]
        # assert "test" in [tag["name"] for tag in result["tags_read"]]
        
        # assert len(result["children_read"]) == 2
        # child_titles = [child["title"] for child in result["children_read"]]
        # assert "First Child Note" in child_titles
        # assert "Second Child Note" in child_titles
        
        # assert len(result["links_read"]) == 2 
        # linked_uuids = [link["uuid"] for link in result["links_read"]]
        # assert notes_for_links[0]["uuid"] in linked_uuids
        # assert notes_for_links[1]["uuid"] in linked_uuids
        # assert "invalid-uuid-123" not in linked_uuids 

        pp("✅ Test passed! Note created with:")
        pp(f'{response.json()}', indent=4)
        # print(f"   - {len(result['tags_read'])} tags")
        # print(f"   - {len(result['children_read'])} children") 
        # print(f"   - {len(result['links_read'])} valid links")
        # print(f"   - Invalid links were ignored (as expected)")

# Запуск теста
if __name__ == "__main__":
    asyncio.run(test_create_note_with_relations())  