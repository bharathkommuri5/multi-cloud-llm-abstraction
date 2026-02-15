from pydantic import BaseModel


class LLMResponse(BaseModel):
    provider: str
    response: str
