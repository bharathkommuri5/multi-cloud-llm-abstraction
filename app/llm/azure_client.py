from openai import AzureOpenAI
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError
from app.core.logger import provider_logger as logger

class AzureOpenAIClient(BaseLLMClient):

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            logger.debug(f"Calling Azure OpenAI ({self.deployment}) with temp={temperature}, max_tokens={max_tokens}")
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            logger.info(f"Azure OpenAI call successful")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI error: {str(e)}")
            raise LLMProviderError(f"Azure OpenAI error: {str(e)}")
