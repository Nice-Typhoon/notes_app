from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, Reminder


async def get_user_notifications(db: AsyncSession, user_id: UUID) -> List[Notification]:
    result = await db.execute(
        select(Notification)
        .options(
            selectinload(Notification.reminder).selectinload(Reminder.note)
        )
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    return list(result.scalars().all())


async def get_unread_notifications_count(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )
    return int(result.scalar_one())


async def get_unread_notifications(db: AsyncSession, user_id: UUID) -> List[Notification]:
    result = await db.execute(
        select(Notification)
        .options(
            selectinload(Notification.reminder).selectinload(Reminder.note)
        )
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .order_by(Notification.created_at.desc())
    )
    return list(result.scalars().all())


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    reminder_id: UUID,
    message: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        reminder_id=reminder_id,
        message=message,
        is_read=False,
    )

    db.add(notification)
    await db.flush()

    return notification


async def mark_all_read(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )


async def mark_one_read(db: AsyncSession, notif_id: UUID, user_id: UUID) -> None:
    await db.execute(
        update(Notification)
        .where(
            Notification.id == notif_id,
            Notification.user_id == user_id,
        )
        .values(is_read=True)
    )
