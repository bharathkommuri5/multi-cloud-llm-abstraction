from app.llm.azure_client import AzureOpenAIClient
from app.llm.bedrock_client import BedrockClient
from app.llm.google_client import GoogleLLMClient
from app.llm.grok_client import GrokClient


def get_llm_client(provider: str):
    provider = provider.lower()

    if provider == "azure":
        return AzureOpenAIClient()
    elif provider == "bedrock":
        return BedrockClient()
    elif provider == "google":
        return GoogleLLMClient()
    elif provider == "grok":
        return GrokClient()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
