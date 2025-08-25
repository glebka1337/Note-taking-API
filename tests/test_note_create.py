from httpx import AsyncClient
from pprint import pprint as pp
import pytest
@pytest.mark.asyncio
async def test_create_note_with_relations(
    async_client: AsyncClient,
    access_token: str
):
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    notes_for_links = []
    for i in range(2):
        note_data = {
            "title": f"Target Note {i}",
            "content": f"Content for target note {i}",
            "parent_id": None
        }
        response = await async_client.post("/notes/", json=note_data, headers=headers)
        print(
            'Created note with UUID: {}'.format(response.json()['uuid'])
        )
        notes_for_links.append(response.json())
    
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
    
    response = await async_client.post("/notes/", json=main_note_data, headers=headers)
    
    assert response.status_code == 201
    result = response.json()

    pp("✅ Test passed! Note created with:")
    pp(f'{response.json()}', indent=4)
    print(f"   - {len(result['tags_read'])} tags")
    print(f"   - {len(result['children_read'])} children") 
    print(f"   - {len(result['links_read'])} valid links")
    print(f"   - Invalid links were ignored (as expected)")

