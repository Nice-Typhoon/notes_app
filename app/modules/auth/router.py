from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.paths import TEMPLATES_DIR
from app.modules.auth.service import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_user_by_email(db, email)
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Пользователь с таким email уже существует"},
        )
    user = User(email=email, full_name=full_name, password_hash=hash_password(password))
    db.add(user)
    await db.flush()
    return RedirectResponse(url="/auth/login?registered=1", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: Optional[str] = None):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"request": request, "error": None, "registered": registered},
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Неверный email или пароль", "registered": None},
        )
    token = create_access_token({"sub": user.email})
    response = RedirectResponse(url="/notes/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response
