from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from uuid import UUID


class HyperparameterConfigCreate(BaseModel):
    model_id: int
    parameters: Dict[str, Any]  # e.g., {"temperature": 0.7, "top_p": 0.9}
    description: str | None = None
    is_default: bool = False


class HyperparameterConfigUpdate(BaseModel):
    parameters: Dict[str, Any] | None = None
    description: str | None = None
    is_default: bool | None = None


class HyperparameterConfigResponse(BaseModel):
    id: int
    user_id: UUID
    model_id: int
    parameters: Dict[str, Any]
    description: str | None
    is_default: bool
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None

    class Config:
        orm_mode = True
