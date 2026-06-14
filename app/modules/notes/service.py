from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Note, Tag


async def get_note_or_404(db: AsyncSession, note_id: UUID, user_id: UUID) -> Note:
    result = await db.execute(
        select(Note)
        .options(selectinload(Note.tags), selectinload(Note.reminders))
        .where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


async def get_user_notes(
    db: AsyncSession,
    user_id: UUID,
    search: Optional[str] = None,
    tag_id: Optional[UUID] = None,
) -> List[Note]:
    query = (
        select(Note)
        .options(selectinload(Note.tags), selectinload(Note.reminders))
        .where(Note.user_id == user_id)
        .order_by(Note.updated_at.desc())
    )
    if search:
        query = query.where(
            or_(Note.title.ilike(f"%{search}%"), Note.content.ilike(f"%{search}%"))
        )
    if tag_id:
        query = query.join(Note.tags).where(Tag.id == tag_id)

    result = await db.execute(query)
    return result.scalars().all()


async def create_note(
        db: AsyncSession,
        user_id: UUID,
        title: str,
        content: str,
        tag_ids: List[str],
) -> Note:
    note = Note(user_id=user_id, title=title.strip(), content=content)

    # Говорим SQLAlchemy: "Эта коллекция пустая, не надо лезть в БД проверять старые связи"
    note.tags = []

    db.add(note)
    await db.flush()

    if tag_ids:
        # Запрашиваем сами теги. selectinload здесь больше не нужен,
        # так как мы присваиваем теги к заметке, а не наоборот.
        tag_result = await db.execute(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        )
        note.tags = list(tag_result.scalars().all())

    return note


async def update_note(
        db: AsyncSession,
        note: Note,
        user_id: UUID,
        title: str,
        content: str,
        tag_ids: List[str],
) -> Note:
    note.title = title.strip()
    note.content = content
    note.updated_at = datetime.now(timezone.utc)

    if tag_ids:
        tag_result = await db.execute(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        )
        # Перезаписываем коллекцию списком новых тегов
        note.tags = list(tag_result.scalars().all())
    else:
        note.tags = []

    return note
