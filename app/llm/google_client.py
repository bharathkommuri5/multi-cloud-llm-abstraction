import google.genai as genai
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError
from app.core.logger import provider_logger as logger

class GoogleLLMClient(BaseLLMClient):
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.error("Google API Key is not configured")
            raise LLMProviderError("Google API Key is not configured")
        
        try:
            # Standard initialization for the modern SDK
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            self.model_id = settings.GOOGLE_MODEL_ID or "gemini-2.0-flash"
            logger.info(f"Google Gemini client initialized (model: {self.model_id})")
        except Exception as e:
            logger.error(f"Could not initialize Gemini client: {e}")
            raise LLMProviderError(f"Could not initialize Gemini client: {e}")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            logger.debug(f"Calling Google Gemini ({self.model_id}) with temp={temperature}, max_tokens={max_tokens}")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            
            if response.text:
                logger.info(f"Google Gemini call successful")
                return response.text
            
            logger.warning("Google Gemini returned an empty response")
            raise LLMProviderError("Gemini returned an empty response (likely blocked).")

        except Exception as e:
            logger.error(f"Google Gemini error: {str(e)}")
            raise LLMProviderError(f"Google AI Error: {str(e)}")