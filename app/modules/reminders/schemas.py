from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ReminderCreate(BaseModel):
    note_id: UUID
    remind_at: datetime


class ReminderRead(BaseModel):
    id: UUID
    note_id: UUID
    remind_at: datetime
    status: str

    model_config = {"from_attributes": True}
