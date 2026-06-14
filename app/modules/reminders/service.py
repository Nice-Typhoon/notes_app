from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note, Reminder


async def get_note_with_reminders(
    db: AsyncSession,
    note_id: UUID,
    user_id: UUID,
) -> Note:
    result = await db.execute(
        select(Note)
        .options(selectinload(Note.reminders))
        .where(
            Note.id == note_id,
            Note.user_id == user_id,
        )
    )

    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


async def create_reminder(
    db: AsyncSession,
    user_id: UUID,
    note_id: UUID,
    remind_at: datetime,
) -> Reminder:
    reminder = Reminder(
        user_id=user_id,
        note_id=note_id,
        remind_at=remind_at,
        status="pending",
    )

    db.add(reminder)
    await db.flush()

    return reminder


async def cancel_reminder(
    db: AsyncSession,
    reminder_id: UUID,
    user_id: UUID,
) -> UUID | None:
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
            Reminder.status == "pending",
        )
    )

    reminder = result.scalar_one_or_none()

    if not reminder:
        return None

    note_id = reminder.note_id
    reminder.status = "cancelled"

    return note_id