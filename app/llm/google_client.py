import google.generativeai as genai
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError


class GoogleLLMClient(BaseLLMClient):

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise LLMProviderError("Google API Key is not configured")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GOOGLE_MODEL_ID or "gemini-pro"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            model = genai.GenerativeModel(self.model)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            
            if response.text:
                return response.text
            else:
                raise LLMProviderError("Empty response from Google Generative AI")
                
        except Exception as e:
            raise LLMProviderError(f"Google Generative AI error: {str(e)}")
