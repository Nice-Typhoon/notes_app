import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.paths import STATIC_DIR
from app.modules.auth.router import router as auth_router
from app.modules.notes.router import router as notes_router
from app.modules.tags.router import router as tags_router
from app.modules.reminders.router import router as reminders_router
from app.modules.notifications.router import router as notifications_router
from app.scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(scheduler_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(title="Notes App", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(reminders_router)
app.include_router(notifications_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/notes/")


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return RedirectResponse(url="/auth/login")
