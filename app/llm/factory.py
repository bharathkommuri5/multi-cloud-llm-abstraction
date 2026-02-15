from app.llm.azure_client import AzureOpenAIClient
from app.llm.bedrock_client import BedrockClient


def get_llm_client(provider: str):
    provider = provider.lower()

    if provider == "azure":
        return AzureOpenAIClient()
    elif provider == "bedrock":
        return BedrockClient()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
