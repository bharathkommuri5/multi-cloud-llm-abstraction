from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID


class LLMRequest(BaseModel):
    user_id: UUID
    provider: str
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 300
    hyperparameter_config_id: int | None = None  # If set, use this config instead of individual params
    custom_parameters: Dict[str, Any] | None = None  # Override specific parameters
