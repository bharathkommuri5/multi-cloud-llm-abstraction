from pydantic import BaseModel,ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

