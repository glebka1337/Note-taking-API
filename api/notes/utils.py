from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.models import Note, Tag
from api.db import get_session

async def get_note_by_id(
    note_id: int,
    db: AsyncSession = Depends(get_session)
) -> Note:
    note_result = await db.execute(
        select(Note).where(Note.id == note_id)
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
