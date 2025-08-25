import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_notes_success(
    async_client: AsyncClient,
    access_token: str
):
    """Test getting a list of notes with default parameters."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create several notes to test the endpoint
    for i in range(5):
        note_data = {
            "title": f"Test Note {i}",
            "content": "Some content.",
            "parent_id": None
        }
        await async_client.post("/notes/", json=note_data, headers=headers)
        
    response = await async_client.get("/notes/", headers=headers)
    
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) == 5
    
    # Check that notes are sorted by updated_at (descending)
    for i in range(len(notes) - 1):
        assert notes[i]['updated_at'] >= notes[i+1]['updated_at']


@pytest.mark.asyncio
async def test_get_notes_with_pagination(
    async_client: AsyncClient,
    access_token: str
):
    """Test pagination with skip and limit parameters."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create 30 notes to test pagination
    for i in range(30):
        note_data = {
            "title": f"Note for Pagination {i}",
            "content": "Content...",
            "parent_id": None
        }
        await async_client.post("/notes/", json=note_data, headers=headers)
    
    # Request first 10 notes
    response = await async_client.get("/notes/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 10
    
    # Request next 5 notes
    response = await async_client.get("/notes/?skip=10&limit=5", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 5
    
    # Test a limit of 100
    response = await async_client.get("/notes/?limit=100", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 30



@pytest.mark.asyncio
async def test_get_notes_filter_by_parent_id(
    async_client: AsyncClient,
    access_token: str
):
    """Test filtering notes by parent_id."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create a parent note
    parent_note_data = {
        "title": "Parent Note",
        "content": "Parent content.",
        "parent_id": None
    }
    parent_response = await async_client.post("/notes/", json=parent_note_data, headers=headers)
    parent_id = parent_response.json()['id']
    
    # Create children notes for the parent
    for i in range(3):
        child_note_data = {
            "title": f"Child Note {i}",
            "content": "Child content.",
            "parent_id": parent_id
        }
        await async_client.post("/notes/", json=child_note_data, headers=headers)
    
    # Create some other top-level notes
    for i in range(2):
        top_level_note_data = {
            "title": f"Top Level Note {i}",
            "content": "Top level content.",
            "parent_id": None
        }
        await async_client.post("/notes/", json=top_level_note_data, headers=headers)
    
    # Get only the child notes
    response = await async_client.get(f"/notes/?parent_id={parent_id}", headers=headers)
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 3
    for note in notes:
        assert note['parent_id'] == parent_id
        
    # Get only the top-level notes
    response = await async_client.get("/notes/", headers=headers)
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 3 # 2 top-level + the original parent note
    for note in notes:
        assert note['parent_id'] is None


@pytest.mark.asyncio
async def test_get_notes_no_notes_found(
    async_client: AsyncClient,
    access_token: str
):
    """Test getting an empty list when no notes are found."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # This test runs on a clean DB, so no notes should exist for the user
    response = await async_client.get("/notes/", headers=headers)
    
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_notes_unauthorized(
    async_client: AsyncClient
):
    """Test getting notes without an access token returns 401."""
    response = await async_client.get("/notes/")
    
    assert response.status_code == 401