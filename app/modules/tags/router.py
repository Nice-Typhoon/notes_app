from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.paths import TEMPLATES_DIR
from app.modules.auth.service import get_current_user
from app.modules.tags.service import create_tag, get_tag_or_404, get_user_tags

router = APIRouter(prefix="/tags", tags=["tags"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def tags_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tags = await get_user_tags(db, current_user.id)
    return templates.TemplateResponse(
        "notes/tags.html",
        {"request": request, "user": current_user, "tags": tags},
    )


@router.post("/create")
async def tag_create(
    name: str = Form(...),
    color: str = Form("#6366f1"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await create_tag(db, current_user.id, name, color)
    return RedirectResponse(url="/tags/", status_code=302)


@router.post("/delete/{tag_id}")
async def tag_delete(
    tag_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tag = await get_tag_or_404(db, tag_id, current_user.id)
    await db.delete(tag)
    return RedirectResponse(url="/tags/", status_code=302)
