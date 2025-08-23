from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.auth.schemas import UserOut
from api.auth.services.auth_service import get_current_user
from api.core.db import get_session
from api.core.models import CrossLink, Note
from api.notes.schemas import NoteRead, NoteCreate, NoteUpdate
from api.notes.service import NoteService
from api.notes.utils import NoteParser, get_note_by_id, get_note_with_relations
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteRead)
async def create_note(
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    try:
        note_data = note_in.model_dump()
        note = Note(**note_data, user_id=user.id, uuid=uuid4())
        db.add(note)
        await db.flush() 

        parser = NoteParser(note.content)
        
        service = NoteService(db)
        service.note = note
        service.parsed_tags = parser.parse_tags()        
        service.parsed_children = parser.parse_children() 
        service.parsed_links = parser.parse_links()    

        await service.handle_note(note)

        await db.commit()
        #  Return the note with relationships loaded
        
        return await get_note_with_relations(
            note_id=note.id, user_id=user.id, db=db
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )



@router.get("/", response_model=list[NoteRead])
async def get_notes(
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    result = await db.execute(select(Note).where(Note.user_id == user.id))
    return result.scalars().all()


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    return await get_note_by_id(note_id, user.id, db)

@router.get("/{title}", response_model=NoteRead)
async def get_note_by_title(): ...

@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    """
    Update a note by ID.

    The note is retrieved from the database and updated with the given data.
    If the content of the note is changed, it is re-parsed and the tags, children and links are updated accordingly.

    Args:
        note_id: The ID of the note to be updated.
        note_in: The data to update the note with.
        db: The database session.
        user: The user who is making the request.

    Returns:
        The updated note.

    Raises:
        HTTPException: If the note is not found or if there is a database error.
    """
    try:
        note = await get_note_by_id(note_id, user.id, db)
        
        old_content = note.content
        
        update_data = note_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(note, key, value)
        
        if "content" in update_data and note.content != old_content:
            parser = NoteParser(note.content)
            
            service = NoteService(db)
            service.note = note
            service.parsed_tags = parser.parse_tags()        
            service.parsed_children = parser.parse_children() 
            service.parsed_links = parser.parse_links()    
            
            await service.handle_note(note)
        
        note.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return await get_note_with_relations(
            note_id=note.id, user_id=user.id, db=db
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update note: {str(e)}"
        )

@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    await db.delete(note)
    await db.commit()
    return {"ok": True}

@router.get("/{note_id}/linked_notes")
async def get_linked_notes(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    result = await db.execute(
        select(Note).where(Note.id.in_([n.id for n in note.linked_notes]))
    )
    notes = result.scalars().all()
    return [{"id": n.id, "slug": n.slug, "title": n.title} for n in notes]

@router.get("/{note_id}/backlinks")
async def get_backlinks(
    note_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note = await get_note_by_id(note_id, user.id, db)
    result = await db.execute(
        select(Note).where(Note.id.in_([n.id for n in note.backlinks]))
    )
    notes = result.scalars().all()
    return [{"id": n.id, "slug": n.slug, "title": n.title} for n in notes]
