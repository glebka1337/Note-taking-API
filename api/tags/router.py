from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from api.auth.schemas import UserOut
from api.core.db import get_session
from api.core.models import Tag
from api.tags.schemas import TagCreate, TagRead
from typing import List
from api.tags.utils import get_tag_by_id
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


@router.get("/{tag_id}", response_model=TagRead)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by_id(tag_id, db, user_id=user.id)
    return tag

@router.put("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: int,
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by_id(tag_id, db, user_id=user.id)
    tag.name = tag_in.name
    await db.commit()
    await db.refresh(tag)
    return tag

@router.delete("/{tag_id}", status_code=status.HTTP_200_OK)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_session),
    user: UserOut = Depends(get_current_user)
):
    tag = await get_tag_by_id(tag_id, db, user_id=user.id)
    await db.delete(tag)
    await db.commit()
    return {"ok": True}
