from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import Tag
from sqlalchemy import select

# ==========================
# Вспомогательная функция
# ==========================
async def get_tag_by_id(tag_id: int, db: AsyncSession) -> Tag:
    tag = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = tag.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

