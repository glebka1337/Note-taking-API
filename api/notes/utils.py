from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.core.models import Note, Tag
from api.core.db import get_session
from typing import Annotated, Dict, List
from api.core.models import note_links
import re
from api.core.models import Note, Tag


class NoteParser:
    """
    Parses tags, inner links and childer notes
    
    parse_tags() -> List[Annotated[str, "Name_of_tag"]]
    parse_links() -> List[Dict[str, str]] [{'title_of_link': 'link_to_another_note'}]
    parse_children() -> List[str] (list of children names)
    """

    def __init__(self, content: str):
        self.content = content

    def parse_tags(self) -> List[str]:
        """
        Returns a list of tag names

        Returns:
            List[str]:
        """
        
        pattern = r'#(\w+)' 
        tags = re.findall(pattern, self.content)
        return [tag for tag in tags]

    def parse_links(self) -> dict[str, str]:
        """
        Parses links like [Title](uuid) and returns {uuid: title}
        """
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, self.content)
        return {m[1].strip(): m[0].strip() for m in matches}

    def parse_children(self) -> List[str]:
        """
        Search for children names in pattern [[ChildName]]
        """
        pattern = r'\[\[(.*?)\]\]'
        matches = re.findall(pattern, self.content)
        return [m.strip() for m in matches]

async def parse_inner_links(s: str):
    "Place holder for some time"
    ...

async def update_note_cross_links(
    note: Note,
    db: AsyncSession
):
    """
    Updates backlinks and linked notes for the given note.
    """
    
    def __delete_links_stmt(
        note_id: int,
        db: AsyncSession
    ):
        """
        Returns a delete statement for removing links related to the note.
        """
        return note_links.delete().where(
            (note_links.c.note_id == note_id)
        )

    # ? Parse inner links from the note content
    inner_links = parse_inner_links(note.content)
    
    if not inner_links:
        # ? So, there are no inner links, we should clear the backlinks and linked notes
        await db.execute(__delete_links_stmt(note.id, db))
        return
    # ? If there are inner links, we should update the backlinks and linked notes
    
    notes_linked_in = await db.execute(
        select(Note).\
        where(
            and_(
                Note.title.in_(inner_links),
                Note.user_id == note.user_id
            )
        )
    )
    
    await db.execute(__delete_links_stmt(note.id, db))
    
    # ? Add links to 
    link_values = [
        {"note_id": note.id, "linked_note_id": linked_note.id}
        for linked_note in notes_linked_in.scalars().all()
    ]
    if link_values:
        await db.execute(note_links.insert(), link_values)
        
async def get_note_by_id(
    note_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_session)
) -> Note:
    note_result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                Note.user_id == user_id
            )
        )
    )
    if not (note_result := note_result.scalar_one_or_none()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note_result

async def attach_tags(note: Note, tag_ids: list[int], db: AsyncSession):
    if not tag_ids:
        note.tags = []
        return
    result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
    note.tags = result.scalars().all()
