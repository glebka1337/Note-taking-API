from api.core.db import async_session
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import CrossLink, note_tags



pytestmark = pytest.mark.asyncio

async def create_note(
    async_client: AsyncClient,
    access_token: str,
    paylad_to_create: dict
):  
    resp = await async_client.post(
        "/notes/",
        json=paylad_to_create,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 201
    return resp.json()

async def delete_note(async_client: AsyncClient, access_token: str, note_uuid: str):
    resp = await async_client.delete(
        url=f"/notes/{note_uuid}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200


async def test_delete_simple_note(
    async_client: AsyncClient,
    access_token: str
):
    
    note = await create_note(async_client, access_token, paylad_to_create={
        "title": "Test Note",
        "content": "Some content.",
    })
    await delete_note(async_client, access_token, note["uuid"])

    # Try fetching deleted note
    resp = await async_client.get(f"/notes/{note['uuid']}", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404


async def test_delete_note_with_children(
    async_client: AsyncClient,
    access_token: str
):
    root_content = \
    """
    Root content
    
    [[Child]]
    """
    root_payload = {
        "title": "Root Note",
        "content": root_content
    }
    
    # crete root note (child will be created automatically)
    root = await create_note(async_client, access_token, paylad_to_create=root_payload)


    child_uuid = root["children_read"][0]["uuid"]
    
    # update child content so it has child also
    
    child_new_content = \
    """
    Child note of root note.
    
    [[ChildChild]]
    """
    
    child_resp = await async_client.put(
        f"/notes/{child_uuid}",
        json={"content": child_new_content},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # get a sub child uuid
    sub_child_uuid = child_resp.json()["children_read"][0]["uuid"]
    
    # delete root note
    await delete_note(async_client, access_token, root["uuid"])

    # root note should be gone
    resp = await async_client.get(f"/notes/{root['uuid']}", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404

    # child note should be gone
    resp = await async_client.get(f"/notes/{child_uuid}", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404

    # sub child note should be gone
    resp = await async_client.get(f"/notes/{sub_child_uuid}", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 404


async def test_delete_note_with_referers_and_refering_to(
    async_client: AsyncClient,
    access_token: str,
    db_connection: AsyncSession
): 
    
    # create a note to which delete note will refer
    note_to_refer_payload = {
        "title": "Note to refer in delete note",
        "content": "Some content.",
        "parent_id": None
    }
    
    note_to_refer = await create_note(async_client, access_token, paylad_to_create=note_to_refer_payload)
    
    note_to_delete_payload = {
        "title": "Note to delete",
        "content":
        f"""
        Delete note content
        
        [Some Title]({note_to_refer['uuid']})
        """,
        "parent_id": None
    }
    
    note_to_delete = await create_note(async_client, access_token, paylad_to_create=note_to_delete_payload)
    
    referer_payload = {
        "title": "Referer Note",
        "content":
        f"""
        Referer Note
        
        [Some Title]({note_to_delete['uuid']})
        """
    }
    
    # create referer note
    
    referer = await create_note(async_client, access_token, paylad_to_create=referer_payload)

    # delete note to delete
    await delete_note(async_client, access_token, note_to_delete["uuid"])

    # check if link were replaced
    
    string_to_check = f"DELETED: {note_to_delete['title']}"
    
    # get referer note, it should contains string_to_check
    
    resp = await async_client.get(f"/notes/{referer['uuid']}", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert string_to_check in resp.json()["content"]
    
    # check if cross link was deleted from table CrossLink
    result = await db_connection.execute(
        select(CrossLink).where(CrossLink.note_id == referer["id"], CrossLink.linked_note_id == note_to_delete["id"])
    )
    cross_links = result.scalars().all()
    assert len(cross_links) == 0
    
    # check if backlink was deleted from table CrossLink
    
    result = await db_connection.execute(
        select(CrossLink).where(CrossLink.note_id == note_to_delete["id"], CrossLink.linked_note_id == note_to_refer["id"])
    )
    cross_links = result.scalars().all()
    assert len(cross_links) == 0

@pytest.mark.asyncio
async def test_delete_full(
    async_client: AsyncClient,
    access_token: str
): 
    # crete note to which delete note will refer  
    note_to_ref_payload = {
        "title": "Note to refer in delete note",
        "content": "Some content.",
        "parent_id": None
    }
    
    note_to_ref_resp = await create_note(async_client, access_token, paylad_to_create=note_to_ref_payload)

    # create root note
    root_payload = {
        "title": "Root Note",
        "content":
        f"""
        Root content
        
        #root_tag
        [Link to note_to_ref]({note_to_ref_resp['uuid']})
        
        [[Child1]]
        [[Child2]]
        """
    }
    root_note_resp = await create_note(async_client, access_token, paylad_to_create=root_payload)

    # create a note that will refer to root note
    referer_payload = {
        "title": "Referer Note",
        "content":
        f"""
        Referer Note
        
        [Link to root]({root_note_resp['uuid']})
        """
    }
    referer_note_resp = await create_note(async_client, access_token, paylad_to_create=referer_payload)

    # create notes that will be refered in child1 and child2
    
    note_to_ref_child1_payload = {
        "title": "Note to refer in child1",
        "content": "Some content.",
    }
    note_to_ref_child1_resp = await create_note(async_client, access_token, paylad_to_create=note_to_ref_child1_payload)

    note_to_ref_child2_payload = {
        "title": "Note to refer in child2",
        "content": "Some content.",
    }
    note_to_ref_child2_resp = await create_note(async_client, access_token, paylad_to_create=note_to_ref_child2_payload)

    child1_uuid = root_note_resp["children_read"][0]["uuid"]
    child2_uuid = root_note_resp["children_read"][1]["uuid"]

    # add child to Child1
    child1_new_content = \
    f"""
    Child1 content
    #child1_tag
    [[Child1_1]]
    
    [Link to note_to_ref_child1]({note_to_ref_child1_resp['uuid']})
    """
    child1_resp = await async_client.put(
        f"/notes/{child1_uuid}",
        json={"content": child1_new_content},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # add child to Child2
    child2_new_content = \
    f"""
    Child2 content
    #child2_tag
    [[Child2_1]]
    
    [Link to note_to_ref_child2]({note_to_ref_child2_resp['uuid']})
    """
    child2_resp = await async_client.put(
        f"/notes/{child2_uuid}",
        json={"content": child2_new_content},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # create referer note pointing to Child1 and Child2
    
    referer_child1_payload = {
        "title": "Referer Note to Child1",
        "content": f"""
        Referer Note
        [Link to child1]({child1_uuid})
        """
    }
    
    referer_child1_resp = await create_note(async_client, access_token, paylad_to_create=referer_child1_payload)
    
    referer_child2_payload = {
        "title": "Referer Note to Child2",
        "content": f"""
        Referer Note
        [Link to child2]({child2_uuid})
        """
    }
    
    referer_child2_resp = await create_note(async_client, access_token, paylad_to_create=referer_child2_payload)
    
    ################
    # Testing part #
    ################
    
    # delete root note
    resp = await async_client.delete(
        f"/notes/{root_note_resp['uuid']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert resp.status_code == 200
    
    # we need to check if the note that refered to root note has changed its links
    
    string_to_check = f'DELETED: {root_note_resp["title"]}'
    
    note_referer_response_new = await async_client.get(
        f"/notes/{referer_note_resp['uuid']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert note_referer_response_new.status_code == 200
    assert string_to_check in note_referer_response_new.json()["content"]

    
    # Check that we do not have any baclinks and linked notes
    
    back_links = await async_client.get(
        f'/notes/{note_to_ref_resp['uuid']}/backlinks', # root note -> note_to_ref
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert back_links.status_code == 200
    assert len(back_links.json()) == 0
    
    # check that we do not have link referer -> root note
    
    referer_back_links = await async_client.get(
        f'/notes/{referer_note_resp["uuid"]}/backlinks', # referer note -> root note
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert referer_back_links.status_code == 200
    assert len(referer_back_links.json()) == 0
    
    # Check that child1 note and child2 were deleted from db
    child1 = await async_client.get(
        f"/notes/{child1_uuid}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    child2 = await async_client.get(
        f"/notes/{child2_uuid}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert child1.status_code == 404
    assert child2.status_code == 404

    # check that referer notes were changed too
    referer_child1 = await async_client.get(
        f"/notes/{referer_child1_resp['uuid']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    referer_child2 = await async_client.get(
        f"/notes/{referer_child2_resp['uuid']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert f'DELETED: {child1_resp.json()["title"]}' in referer_child1.json()["content"]
    assert f'DELETED: {child2_resp.json()["title"]}' in referer_child2.json()["content"]

    # # Check that note_to_ref_child1 and note_to_ref_child2 crosslinks were deleted
    
    backlinks_child1_response = await async_client.get(
        f"/notes/{note_to_ref_child1_resp['uuid']}/backlinks",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert backlinks_child1_response.status_code == 200
    assert len(backlinks_child1_response.json()) == 0
    
    backlinks_child2_response = await async_client.get(
        f"/notes/{note_to_ref_child2_resp['uuid']}/backlinks",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert backlinks_child2_response.status_code == 200
    assert len(backlinks_child2_response.json()) == 0
   
    # Check database note_tags were deleted
    
    root_tag_uuid = root_note_resp["tags_read"][0]["uuid"]

    root_tag_response = await async_client.get(
        f"/tags/{root_tag_uuid}/notes",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    # should be empty
    assert root_tag_response.status_code == 200
    assert len(root_tag_response.json()) == 0
    
    child1_tag_uuid = child1_resp.json()["tags_read"][0]["uuid"]
    
    child1_tags_response = await async_client.get(
        f"/tags/{child1_tag_uuid}/notes",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert child1_tags_response.status_code == 200
    assert len(child1_tags_response.json()) == 0

    child2_tag_uuid = child2_resp.json()["tags_read"][0]["uuid"]
    
    child2_tags_response = await async_client.get(
        f"/tags/{child2_tag_uuid}/notes",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert child2_tags_response.status_code == 200
    assert len(child2_tags_response.json()) == 0
    