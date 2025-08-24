from typing import Any, List
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.core.db import get_session
from api.core.models import Note
from sqlalchemy.orm import selectinload
from api.core.models import CrossLink

async def get_note_with_relations(
    note_uuid: str,
    user_id: int,
    db: AsyncSession = Depends(get_session)
) -> Note:
    """
    Loads a note with all its relationships using eager loading to avoid N+1 queries.
    """
    result = await db.execute( 
        select(Note)
        .where(Note.uuid == note_uuid, Note.user_id == user_id)
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

valid_fields = [column.name for column in Note.__table__.columns]

async def get_note_by(
    field_name: str,
    field_value: Any,
    user_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get note by field given
    
    Args:
        field_name: The name of the field to get the note by
        field_value: The value of the field to get the note by
        user_id: The id of the user who is making the request
        db: The database session
    
    Returns:
        Note: The note found
    Raises:
        HTTPException: If the note is not found with code 404
    """
    
    if field_name not in valid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field name: {field_name}. Valid fields are: {', '.join(valid_fields)}"
        )
    
    result = await db.execute(
        select(Note).where(getattr(Note, field_name) == field_value, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note not found"
        )
    
    return note