from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import Tag
from sqlalchemy import and_, select


async def get_tag_by_id(tag_id: int, db: AsyncSession, user_id: int) -> Tag:
    tag = await db.execute(select(Tag).where(
        and_(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    ))
    
    tag = tag.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

