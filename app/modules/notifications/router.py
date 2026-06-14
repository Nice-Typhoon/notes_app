from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.modules.auth.service import get_current_user
from app.modules.notifications.service import (
    get_unread_notifications,
    get_user_notifications,
    get_unread_notifications_count,
    mark_all_read,
    mark_one_read,
)
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Moscow")
router = APIRouter(prefix="/notifications", tags=["notifications"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def notifications_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications = await get_user_notifications(db, current_user.id)
    unread_count = await get_unread_notifications_count(db, current_user.id)

    return templates.TemplateResponse(
        "notifications/list.html",
        {
            "request": request,
            "user": current_user,
            "notifications": notifications,
            "unread_count": unread_count,
            "local_tz": LOCAL_TZ,
        },
    )


@router.get("/unread")
async def notifications_unread(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications = await get_unread_notifications(db, current_user.id)

    return {
        "unread_count": len(notifications),
        "notifications": [
            {
                "id": str(notification.id),
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
                "note_id": (
                    str(notification.reminder.note_id)
                    if notification.reminder
                    else None
                ),
            }
            for notification in notifications
        ],
    }


@router.post("/{notif_id}/read")
async def notification_read(
    notif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_one_read(db, notif_id, current_user.id)
    return RedirectResponse(url="/notifications/", status_code=302)


@router.post("/read-all")
async def notifications_read_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_all_read(db, current_user.id)
    return RedirectResponse(url="/notifications/", status_code=302)
