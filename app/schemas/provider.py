from pydantic import BaseModel
from datetime import datetime

class ProviderCreate(BaseModel):
    name: str
    type: str  # azure / bedrock / google

class ProviderResponse(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        orm_mode = True
