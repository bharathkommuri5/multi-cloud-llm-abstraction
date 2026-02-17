from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

class LLMCallHistoryCreate(BaseModel):
    prompt: str
    response: str
    parameters_used: Dict[str, Any] | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    total_tokens: int | None = None
    cost: float | None = None
    status: str = "success"
    error_message: str | None = None


class LLMCallHistoryResponse(BaseModel):
    id: int
    user_id: UUID
    provider_id: int
    model_id: int
    prompt: str
    response: str
    parameters_used: Dict[str, Any] | None
    tokens_input: int | None
    tokens_output: int | None
    total_tokens: int | None
    cost: float | None
    status: str
    error_message: str | None
    created_at: datetime | None
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LLMCallHistoryFilter(BaseModel):
    user_id: UUID | None = None
    provider_id: int | None = None
    model_id: int | None = None
    status: str | None = None
