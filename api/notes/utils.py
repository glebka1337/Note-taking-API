from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.core.models import Note, Tag
from api.core.db import get_session
from typing import List, Optional
import re
from api.core.models import Note, CrossLink
from sqlalchemy.orm import selectinload

from api.notes.schemas import NoteChildRead, NoteLinkRead, NoteRead, NoteTagRead



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
        """
        pattern = r'#([a-zA-Z0-9_]+)'
        tags = re.findall(pattern, self.content)
        return [tag for tag in tags if tag] 

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
    result = await db.execute(  # ← сохраняем как result
        select(Note)
        .where(Note.id == note_id, Note.user_id == user_id)
        .options(
            selectinload(Note.children),
            selectinload(Note.tags),
            selectinload(Note.linked_notes).joinedload(CrossLink.linked_note),
        )
    )
    note = result.scalar_one_or_none()  
    
    if not note:
        return None
    
    return note 

def create_note_read_response(note_obj: Note) -> NoteRead:
    children = [
            NoteChildRead(
                uuid=child.uuid,  
                title=child.title,
            ) for child in note_obj.children
        ] if note_obj.children else []
    
    tags = [
            NoteTagRead(
                uuid=tag.uuid,  
                name=tag.name,
            ) for tag in note_obj.tags
        ] if note_obj.tags else []
    
    links = [
            NoteLinkRead(
                linked_note_uuid=link.linked_note.uuid if link.linked_note else None,
                title=link.title,
            ) for link in note_obj.linked_notes
        ] if note_obj.linked_notes else []
    
    return NoteRead(
        id=note_obj.id,
        uuid=note_obj.uuid,
        title=note_obj.title,
        content=note_obj.content,
        created_at=note_obj.created_at,
        updated_at=note_obj.updated_at,
        user_id=note_obj.user_id,
        parent_id=note_obj.parent_id,
        children_read=children,
        tags_read=tags,
        links_read=links
    )
    
async def check_note_title_unique(
    title: str,
    parent_id: Optional[int],
    user_id: int,
    db: AsyncSession
) -> bool:
    """
    Checks if a note with given title, parent_id and user_id already exists in the database.
    Returns True if it does not exist, False otherwise.
    """
    query = select(Note).where(
        Note.title == title,
        Note.user_id == user_id,
        Note.parent_id == parent_id
    )
    
    result = await db.execute(query)
    existing_note = result.scalar_one_or_none()
    
    return existing_note is None