from pydantic import BaseModel


class LLMRequest(BaseModel):
    provider: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 300
