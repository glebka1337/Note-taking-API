import uuid
import pytest
from httpx import AsyncClient
from pprint import pprint as pp

@pytest.mark.asyncio
async def test_update_note_content_with_relations(
    async_client: AsyncClient,
    access_token: str
):
    """Test updating note content and verifying relations are updated"""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Create target notes for links
    target_notes = []
    for i in range(2):
        note_data = {
            "title": f"Target Note {i}",
            "content": f"Content for target note {i}",
            "parent_id": None
        }
        response = await async_client.post("/notes/", json=note_data, headers=headers)
        target_notes.append(response.json())
    
    # 2. Create main note with initial content
    initial_content = f"""
    Initial content with:
    #oldtag
    [[Old Child Note]]
    [old-link]({target_notes[0]['uuid']})
    """
    
    main_note_data = {
        "title": "Main Test Note",
        "content": initial_content,
        "parent_id": None
    }
    
    create_response = await async_client.post("/notes/", json=main_note_data, headers=headers)
    assert create_response.status_code == 201
    main_note = create_response.json()
    
    # 3. Update note content with new relations
    updated_content = f"""
    Updated content with new relations!
    
    New tags:
    #newtag 
    #important
    
    New children:
    [[New Child Note 1]]
    [[New Child Note 2]]
    
    New links:
    [new-link-1]({target_notes[0]['uuid']})
    [new-link-2]({target_notes[1]['uuid']})
    """
    
    update_data = {
        "title": "Updated Main Note Title",
        "content": updated_content
    }
    
    # 4. Send update request
    update_response = await async_client.put(
        f"/notes/{main_note['uuid']}",
        json=update_data,
        headers=headers
    )
    
    assert update_response.status_code == 200
    updated_note = update_response.json()
    
    # 5. Verify the updates
    assert updated_note['title'] == "Updated Main Note Title"
    
    # Check tags were updated
    tag_names = [tag['name'] for tag in updated_note['tags_read']]
    assert "newtag" in tag_names
    assert "important" in tag_names
    assert "oldtag" not in tag_names  # old tag should be removed
    
    # Check children were updated  
    child_titles = [child['title'] for child in updated_note['children_read']]
    assert "New Child Note 1" in child_titles
    assert "New Child Note 2" in child_titles
    assert "Old Child Note" not in child_titles  # old child should be removed
    
    # Check links were updated
    link_titles = [link['title'] for link in updated_note['links_read']]
    assert "new-link-1" in link_titles
    assert "new-link-2" in link_titles
    assert "old-link" not in link_titles  # old link should be removed

@pytest.mark.asyncio
async def test_update_note_title_only(
    async_client: AsyncClient,
    access_token: str
):
    """Test updating only title without changing content and relations"""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create a test note
    note_data = {
        "title": "Original Title",
        "content": "Content with #tag and [[Child Note]]",
        "parent_id": None
    }
    
    create_response = await async_client.post("/notes/", json=note_data, headers=headers)
    assert create_response.status_code == 201
    original_note = create_response.json()
    
    # Update only the title
    update_data = {"title": "New Title Only"}
    
    update_response = await async_client.put(
        f"/notes/{original_note['uuid']}",
        json=update_data,
        headers=headers
    )
    
    assert update_response.status_code == 200
    updated_note = update_response.json()
    
    # Verify only title changed
    assert updated_note['title'] == "New Title Only"
    assert updated_note['content'] == original_note['content']  # unchanged
    assert len(updated_note['tags_read']) == 1  # unchanged
    assert len(updated_note['children_read']) == 1  # unchanged

@pytest.mark.asyncio
async def test_update_note_with_non_existent_uuid(
    async_client: AsyncClient,
    access_token: str
):
    """Test updating a non-existent note (with a valid UUID) returns 404"""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    update_data = {
        "title": "New Title",
        "content": "New content"
    }
    
    non_existent_uuid = str(uuid.uuid4())
    
    response = await async_client.put(
        f"/notes/{non_existent_uuid}",
        json=update_data,
        headers=headers
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_note_duplicate_title(
    async_client: AsyncClient,
    access_token: str
):
    """Test updating note title to duplicate in same folder returns error"""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create first note
    note1_data = {
        "title": "Unique Title",
        "content": "Content 1",
        "parent_id": None
    }
    response1 = await async_client.post("/notes/", json=note1_data, headers=headers)
    assert response1.status_code == 201
    
    # Create second note with different title
    note2_data = {
        "title": "Different Title", 
        "content": "Content 2",
        "parent_id": None
    }
    response2 = await async_client.post("/notes/", json=note2_data, headers=headers)
    assert response2.status_code == 201
    note2 = response2.json()
    
    # Try to update second note to have same title as first
    update_data = {"title": "Unique Title"}
    
    update_response = await async_client.put(
        f"/notes/{note2['uuid']}",
        json=update_data,
        headers=headers
    )
    
    # Should return 400 for duplicate title
    assert update_response.status_code == 400

@pytest.mark.asyncio
async def test_update_note_empty_content(
    async_client: AsyncClient,
    access_token: str
):
    """Test updating note with empty content clears relations"""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create note with relations
    note_data = {
        "title": "Note with relations",
        "content": "Content with #tag and [[Child Note]]",
        "parent_id": None
    }
    
    create_response = await async_client.post("/notes/", json=note_data, headers=headers)
    assert create_response.status_code == 201
    original_note = create_response.json()
    
    # Verify it has relations initially
    assert len(original_note['tags_read']) == 1
    assert len(original_note['children_read']) == 1
    
    # Update with empty content
    update_data = {"content": ""}
    
    update_response = await async_client.put(
        f"/notes/{original_note['uuid']}",
        json=update_data,
        headers=headers
    )
    
    assert update_response.status_code == 200
    updated_note = update_response.json()
    
    # Relations should be cleared
    assert updated_note['content'] == ""
    assert len(updated_note['tags_read']) == 0
    assert len(updated_note['children_read']) == 0