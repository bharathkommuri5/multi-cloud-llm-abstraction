from pydantic import BaseModel
from datetime import datetime

class ModelCreate(BaseModel):
    name: str
    provider_id: int

class ModelResponse(BaseModel):
    id: int
    name: str
    provider_id: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        orm_mode = True

