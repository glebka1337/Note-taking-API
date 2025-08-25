

from httpx import AsyncClient


async def create_test_note_hierarchy(
    async_client: AsyncClient, headers: dict[str, str]
):
    
    # create note that note to delete will refer to
    # noteTodelete -> noteref1
    
    note_ref_to_content = \
    """
    Delete note will refer to this note
    """
    
    response = await async_client.post(
        json={
            "title": "NoteRefTitle1",
            "content": note_ref_to_content
        },
        url='/notes/',
        headers=headers
    )
    
    note_ref_to_uuid = response.json()['uuid']
    note_ref_title = response.json()['title']
    # Create NoteToDelete
    
    note_to_delete_content = \
    f"""
    NoteToDetete
    
    [[Child1]]
    [[Child2]]
    
    [{note_ref_title}]({note_ref_to_uuid})
    
    #tag1
    #tag2
    """

    response = await async_client.post(
        json={
            "title": "NoteToDelete",
            "content": note_to_delete_content
        },
        url='/notes/',
        headers=headers
    )
    
    # create childs for childs in note to delete
    
    child_uuid1 = response.json()['children_read'][0].uuid
    child_uuid2 = response.json()['children_read'][1].uuid
    
    response_child1 = await async_client.put(
        json={
            "title": "Child1",
            "content":  \
            """
            Child1
            
            #tagchild1
            
            [[ChildChild1]]
            """
        },
        url=f'/notes/{child_uuid1}',
        headers=headers
    )
    
    response_child2 = await async_client.put(
        json={
            "title": "Child2",
            "content":  \
            """
            Child2
            
            #tagchild2
            
            [[ChildChild2]]
            """
        },
        url=f'/notes/{child_uuid2}',
        headers=headers
    )
    # crete notes to which children and sub children will refer to
    
    for i in range(2, 4):
        # creates 3 notes to which children and sub children will refer to
        response = await async_client.post(
            json={
                "title": f"NoteRef{i}",
                "content": note_ref_to_content
            },
            url='/notes/',
            headers=headers
        )
    
    # update childs of childs so they have tags
    
    child_child_uuid1 = response_child1.json()['children_read'][0].uuid
    child_child_uuid2 = response_child2.json()['children_read'][0].uuid
    
    response_child_child1 = async_client.put(
        json={
            "title": "ChildChild1",
            "content":  \
            """
            ChildChild1
            
            #tagchildchild1
            """
        },
        url=f'/notes/{child_uuid2}',
        headers=headers
    )
    
    response_child_child1 = async_client.put(
        json={
            "title": "ChildChild2",
            "content":  \
            """
            ChildChild2
            
            #tagchildchild2
            """
        },
        url=f'/notes/{child_uuid2}',
        headers=headers
    )