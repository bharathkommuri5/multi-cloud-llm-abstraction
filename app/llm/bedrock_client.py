import json
import boto3
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError
from app.core.logger import provider_logger as logger

class BedrockClient(BaseLLMClient):

    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            logger.debug(f"Calling AWS Bedrock ({self.model_id}) with temp={temperature}, max_tokens={max_tokens}")
            body = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            logger.info(f"AWS Bedrock call successful")
            return response_body["content"][0]["text"]

        except Exception as e:
            logger.error(f"AWS Bedrock error: {str(e)}")
            raise LLMProviderError(f"AWS Bedrock error: {str(e)}")
