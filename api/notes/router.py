from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID, select
from api.auth.schemas import UserOut
from api.auth.services.auth_service import get_current_user
from api.core.db import get_session
from api.core.models import CrossLink, Note, note_tags
from api.notes.schemas import NoteCrossLinkRead, NoteRead, NoteCreate, NoteShallowRead, NoteTagAssociationRead, NoteTagRead, NoteUpdate
from api.notes.services.note_delete_service import NoteDeleteService
from api.notes.services.note_service import NoteService
from api.notes.utils import NoteParser, check_note_title_unique_or_400, create_note_read_response
from api.notes.crud import get_note_with_relations, get_note_by


router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    try:
        await check_note_title_unique_or_400(
            note_in.title,
            parent_id=note_in.parent_id if note_in.parent_id else None,
            user_id=user.id,
            db=db
        )
        
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
        await db.refresh(note)
        
        note_obj = await get_note_with_relations(note.uuid, user.id, db)
        
        return create_note_read_response(note_obj)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get("/", response_model=list[NoteShallowRead])
async def get_notes(
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
    parent_id: Optional[int] = None,
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of items to return")] = 20,
):
    """
    Get paginated list of notes with basic info (no content, tags, children, links).
    """
    query = (
        select(Note)
        .where(
            Note.user_id == user.id,
            Note.parent_id == parent_id
        )
        .order_by(Note.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{note_uuid}", response_model=NoteRead)
async def get_note(
    note_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    note_obj = await get_note_with_relations(note_uuid, user.id, db)
    
    if note_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return create_note_read_response(note_obj)


@router.put("/{note_uuid}", response_model=NoteRead)
async def update_note(
    note_uuid: UUID,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    """
    Update note with given uuid.

    Updates note with given uuid and given fields. If content is updated, note's tags, children, and links are also updated.

    Args:
        note_uuid (str): The uuid of the note to update.
        note_in (NoteUpdate): The fields to update.

    Returns:
        NoteRead: The updated note.
    """
    try:
        
        
        await check_note_title_unique_or_400(
            note_in.title,
            parent_id=note_in.parent_id if note_in.parent_id else None,
            user_id=user.id,
            db=db
        )
        
        note = await get_note_by("uuid", note_uuid, user.id, db)
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
        
        note_obj =  await get_note_with_relations(
            note_uuid, user_id=user.id, db=db
        )
        
        return create_note_read_response(note_obj)
    
    except HTTPException:
        # Re-raise explicit HTTP exceptions
        raise
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update note: {str(e)}"
        )

########################
#! Will be added later #
########################
@router.delete("/{note_uuid}")
async def delete_note(
    note_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    """
    Deletes a note by its UUID and all related entities (children, tags, links).
    """

    # Check if note with given uuid exists
    
    note = await get_note_by("uuid", note_uuid, user.id, db)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    delete_service = NoteDeleteService(db)

    await delete_service.delete_note(
        note_to_delete=note
    )
    
    return {"message": "Note deleted successfully."}

@router.get('/{note_uuid}/backlinks', response_model=list[NoteCrossLinkRead])
async def get_note_backlinks(
    note_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
    
):
    """
    Returns a list of notes that refer to the note with the given uuid
    """
    note = await get_note_by("uuid", note_uuid, user.id, db)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    backlinks = await db.execute(
        select(CrossLink).\
            where(
                CrossLink.linked_note_id == note.id,
            )
    )
    return backlinks

@router.get('/{note_uuid}/linked_notes', response_model=list[NoteCrossLinkRead])
async def get_note_referers(
    note_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
    
):
    """
    Returns a list of notes that the note with the given uuid refers to
    """
    note = await get_note_by("uuid", note_uuid, user.id, db)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    referers = await db.execute(
        select(CrossLink).\
            where(
                CrossLink.note_id == note.id,
            )
    )
    return referers.scalars().all()

@router.get('/{note_uuid}/tags', response_model=list[NoteTagAssociationRead])
async def get_note_tags(
    note_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
): 
    """
    Return a list of tags associated with a note
    """
    
    note = await get_note_by("uuid", note_uuid, user.id, db)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    tags = await db.execute(
        select(note_tags).\
            where(
                note_tags.c.note_id == note.id,
            )
    )
    return tags.scalars().all()