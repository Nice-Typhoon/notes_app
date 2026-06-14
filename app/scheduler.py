"""Async scheduler: periodically checks pending reminders and creates notifications."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Reminder
from app.modules.notifications.service import create_notification

logger = logging.getLogger(__name__)


async def process_reminders() -> None:
    """Fire all pending reminders whose remind_at <= now."""
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            result = await db.execute(
                select(Reminder)
                .options(selectinload(Reminder.note))
                .where(
                    Reminder.status == "pending",
                    Reminder.remind_at <= now,
                )
            )

            due_reminders = list(result.scalars().all())

            for reminder in due_reminders:
                note_title = reminder.note.title if reminder.note else "заметка удалена"

                await create_notification(
                    db=db,
                    user_id=reminder.user_id,
                    reminder_id=reminder.id,
                    message=f"Напоминание: «{note_title}»",
                )

                reminder.status = "fired"

                logger.info(
                    "Fired reminder %s for user %s",
                    reminder.id,
                    reminder.user_id,
                )

            await db.commit()


        except Exception:
            logger.exception("Scheduler error")
            await db.rollback()


async def scheduler_loop() -> None:
    """Run process_reminders on a fixed interval."""
    logger.info(
        "Scheduler started, interval=%s seconds",
        settings.SCHEDULER_INTERVAL_SECONDS,
    )

    while True:
        await process_reminders()
        await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)