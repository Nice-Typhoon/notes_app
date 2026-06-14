from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.paths import TEMPLATES_DIR
from app.modules.auth.service import get_current_user
from app.modules.notifications.service import get_unread_notifications_count
from app.modules.reminders.service import (
    cancel_reminder,
    create_reminder,
    get_note_with_reminders,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
LOCAL_TZ = ZoneInfo("Europe/Moscow")

@router.get("/note/{note_id}", response_class=HTMLResponse)
async def reminder_page(
    note_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_with_reminders(db, note_id, current_user.id)
    unread_count = await get_unread_notifications_count(db, current_user.id)

    reminders = [
        reminder
        for reminder in note.reminders
        if reminder.status != "cancelled"
    ]

    return templates.TemplateResponse(
        "reminders/manage.html",
        {
            "request": request,
            "user": current_user,
            "note": note,
            "reminders": reminders,
            "now": datetime.now(timezone.utc),
            "local_tz": LOCAL_TZ,
            "error": None,
            "unread_count": unread_count,
        },
    )


@router.post("/note/{note_id}/create")
async def reminder_create(
    note_id: UUID,
    request: Request,
    remind_at: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_with_reminders(db, note_id, current_user.id)
    unread_count = await get_unread_notifications_count(db, current_user.id)

    try:
        remind_local = datetime.fromisoformat(remind_at)

        if remind_local.tzinfo is None:
            remind_local = remind_local.replace(tzinfo=LOCAL_TZ)

        remind_dt = remind_local.astimezone(timezone.utc)

    except ValueError:
        active = [r for r in note.reminders if r.status != "cancelled"]
        return templates.TemplateResponse(
            "reminders/manage.html",
            {
                "request": request,
                "user": current_user,
                "note": note,
                "reminders": active,
                "now": datetime.now(timezone.utc),
                "error": "Неверный формат даты и времени",
            },
        )

    if remind_dt <= datetime.now(timezone.utc):
        reminders = [
            reminder
            for reminder in note.reminders
            if reminder.status != "cancelled"
        ]

        return templates.TemplateResponse(
            "reminders/manage.html",
            {
                "request": request,
                "user": current_user,
                "note": note,
                "reminders": reminders,
                "now": datetime.now(timezone.utc),
                "error": "Дата напоминания должна быть в будущем",
                "unread_count": unread_count,
            },
        )

    await create_reminder(
        db=db,
        user_id=current_user.id,
        note_id=note_id,
        remind_at=remind_dt,
    )

    return RedirectResponse(url=f"/reminders/note/{note_id}", status_code=302)


@router.post("/{reminder_id}/cancel")
async def reminder_cancel(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note_id = await cancel_reminder(db, reminder_id, current_user.id)

    if note_id:
        return RedirectResponse(url=f"/reminders/note/{note_id}", status_code=302)

    return RedirectResponse(url="/notes/", status_code=302)
