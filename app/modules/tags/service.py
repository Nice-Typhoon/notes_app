from __future__ import annotations
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tag


async def get_user_tags(db: AsyncSession, user_id: UUID) -> List[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
    )
    return result.scalars().all()


async def get_tag_or_404(db: AsyncSession, tag_id: UUID, user_id: UUID) -> Tag:
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


async def create_tag(db: AsyncSession, user_id: UUID, name: str, color: str) -> Tag:
    tag = Tag(user_id=user_id, name=name.strip(), color=color)
    db.add(tag)
    await db.flush()
    return tag
