from typing import Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.models import Tag
from sqlalchemy import and_, select


valid_fields = [column.name for column in Tag.__table__.columns]

async def get_tag_by(
    field_name: str,
    field_value: Any,
    user_id: int,
    db: AsyncSession
) -> Tag:
    # check if given field name even exists
    if field_name not in valid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field name: {field_name}. Valid fields are: {', '.join(valid_fields)}"
        )
    result = await db.execute(
        select(Tag).where(
            and_(
                getattr(Tag, field_name) == field_value,
                Tag.user_id == user_id
            )
        )
    )
    tag = result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with {field_name} {field_value} not found"
        )
    return tag