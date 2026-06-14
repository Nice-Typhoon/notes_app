from uuid import UUID
from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class TagRead(BaseModel):
    id: UUID
    name: str
    color: str

    model_config = {"from_attributes": True}
