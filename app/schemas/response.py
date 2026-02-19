from pydantic import BaseModel


class LLMResponse(BaseModel):
    provider: str
    model: str
    response: str
    history_id: int | None = None
