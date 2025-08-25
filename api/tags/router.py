from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from api.auth.schemas import UserOut
from api.core.db import get_session
from api.core.models import Note, Tag, note_tags
from api.notes.schemas import NoteShallowRead
from api.tags.schemas import TagCreate, TagRead
from typing import List
from api.tags.utils import get_tag_by
from api.auth.services.auth_service import get_current_user

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
)

@router.post("/", response_model=TagRead)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):

    existing_tag = await db.execute(select(Tag).where(
        and_(
            Tag.name == tag_in.name,
            Tag.user_id == user.id
        )
    ))
    
    if existing_tag.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists"
        )
    tag = Tag(
        name=tag_in.name,
        user_id=user.id
    )
    
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

@router.get("/", response_model=List[TagRead])
async def get_tags(
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    result = await db.execute(select(Tag).where(Tag.user_id == user.id))
    return result.scalars().all()


@router.get("/{tag_uuid}", response_model=TagRead)
async def get_tag(
    tag_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by("uuid", tag_uuid, user_id=user.id, db=db)
    return tag

@router.put("/{tag_uuid}", response_model=TagRead)
async def update_tag(
    tag_uuid: UUID,
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by("uuid", tag_uuid, user_id=user.id, db=db)
    tag.name = tag_in.name
    await db.commit()
    await db.refresh(tag)
    return tag

@router.delete("/{tag_uuid}", status_code=status.HTTP_200_OK)
async def delete_tag(
    tag_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by("uuid", tag_uuid, user_id=user.id, db=db)
    await db.delete(tag)
    await db.commit()
    return {"ok": True}


@router.get('/{tag_uuid}/notes', response_model=list[NoteShallowRead])
async def get_tag_notes(
    tag_uuid: UUID,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user),
):
    """
    Returns a list of notes associated with the given tag uuid.
    """
    tag = await get_tag_by("uuid", tag_uuid, user_id=user.id, db=db)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    notes_stmt = select(Note).join(note_tags).where(note_tags.c.tag_id == tag.id)
    result = await db.execute(notes_stmt)
    notes = result.scalars().all()
    
    return notes