import requests
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError
from app.core.logger import provider_logger as logger

class GrokClient(BaseLLMClient):

    def __init__(self):
        if not settings.GROK_API_KEY or not settings.GROK_API_URL:
            raise LLMProviderError("Grok API is not configured")

        self.api_key = settings.GROK_API_KEY
        self.api_url = settings.GROK_API_URL
        self.model = settings.GROK_MODEL_ID

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            logger.debug(f"Calling Grok ({self.model}) via {self.api_url} with temp={temperature}, max_tokens={max_tokens}")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "input": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            logger.info(f"Grok call successful")

            # Try to extract common fields; fall back to raw text
            data = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else {}

            # Common response shapes: {"text": "..."}, {"output": "..."}, {"choices":[{"text": "..."}]}
            if isinstance(data, dict):
                if data.get("text"):
                    return data.get("text")
                if data.get("output"):
                    return data.get("output")
                if data.get("choices") and isinstance(data.get("choices"), list):
                    first = data.get("choices")[0]
                    if isinstance(first, dict) and first.get("text"):
                        return first.get("text")

            # Fallback to plain text body
            return resp.text

        except Exception as e:
            logger.error(f"Grok provider error: {str(e)}")
            raise LLMProviderError(f"Grok provider error: {str(e)}")
