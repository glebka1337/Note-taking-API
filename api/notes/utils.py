from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.core.models import Note, Tag
from api.core.db import get_session
from typing import List
import re
from api.core.models import Note, CrossLink
from sqlalchemy.orm import selectinload



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

async def get_note_by_id(
    note_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_session)    
) -> Note:
    result = await db.execute(
        select(Note).where(and_(Note.id == note_id, Note.user_id == user_id))
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note

async def get_note_with_relations(
    note_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_session)
) -> Note:
    """
    Loads a note with all its relationships using eager loading to avoid N+1 queries.
    """
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id, Note.user_id == user_id)
        .options(
            selectinload(Note.children),
            selectinload(Note.tags),
            selectinload(Note.linked_notes).joinedload(CrossLink.linked_note),
        )
    )
    return result.scalar_one()