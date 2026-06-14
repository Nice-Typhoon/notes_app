from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.paths import TEMPLATES_DIR
from app.modules.auth.service import get_current_user
from app.modules.tags.service import get_user_tags
from app.modules.notes.service import (
    get_note_or_404,
    get_user_notes,
    create_note,
    update_note,
)
from zoneinfo import ZoneInfo
from app.modules.notifications.service import get_unread_notifications_count

router = APIRouter(prefix="/notes", tags=["notes"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
LOCAL_TZ = ZoneInfo("Europe/Moscow")

@router.get("/", response_class=HTMLResponse)
async def notes_list(
    request: Request,
    search: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notes = await get_user_notes(db, current_user.id, search=search, tag_id=tag_id)
    tags = await get_user_tags(db, current_user.id)
    unread_count = await get_unread_notifications_count(db, current_user.id)

    return templates.TemplateResponse(
        "notes/list.html",
        {
            "request": request,
            "user": current_user,
            "notes": notes,
            "tags": tags,
            "search": search or "",
            "active_tag": str(tag_id) if tag_id else None,
            "unread_count": unread_count,
            "local_tz": LOCAL_TZ
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def note_new_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tags = await get_user_tags(db, current_user.id)
    return templates.TemplateResponse(
        "notes/edit.html",
        {"request": request, "user": current_user, "note": None, "tags": tags, "error": None, "local_tz": LOCAL_TZ},
    )


@router.post("/new")
async def note_create(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    tag_ids: List[str] = Form([]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not title.strip():
        tags = await get_user_tags(db, current_user.id)
        return templates.TemplateResponse(
            "notes/edit.html",
            {"request": request, "user": current_user, "note": None, "tags": tags, "local_tz": LOCAL_TZ,
             "error": "Заголовок не может быть пустым"},
        )
    await create_note(db, current_user.id, title, content, tag_ids)
    return RedirectResponse(url="/notes/", status_code=302)


@router.get("/{note_id}/edit", response_class=HTMLResponse)
async def note_edit_page(
    note_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_or_404(db, note_id, current_user.id)
    tags = await get_user_tags(db, current_user.id)
    return templates.TemplateResponse(
        "notes/edit.html",
        {"request": request, "user": current_user, "note": note, "tags": tags, "local_tz": LOCAL_TZ, "error": None},
    )


@router.post("/{note_id}/edit")
async def note_update(
    note_id: UUID,
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    tag_ids: List[str] = Form([]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_or_404(db, note_id, current_user.id)
    if not title.strip():
        tags = await get_user_tags(db, current_user.id)
        return templates.TemplateResponse(
            "notes/edit.html",
            {"request": request, "user": current_user, "note": note, "tags": tags, "local_tz": LOCAL_TZ,
             "error": "Заголовок не может быть пустым"},
        )
    await update_note(db, note, current_user.id, title, content, tag_ids)
    return RedirectResponse(url="/notes/", status_code=302)


@router.post("/{note_id}/delete")
async def note_delete(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await get_note_or_404(db, note_id, current_user.id)
    await db.delete(note)
    return RedirectResponse(url="/notes/", status_code=302)
