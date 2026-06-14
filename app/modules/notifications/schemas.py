from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: UUID
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
