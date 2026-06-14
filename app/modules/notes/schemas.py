from __future__ import annotations
from typing import List
from uuid import UUID

from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    content: str = ""
    tag_ids: List[UUID] = []


class NoteUpdate(BaseModel):
    title: str
    content: str = ""
    tag_ids: List[UUID] = []
