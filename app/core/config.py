import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Azure
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    # AWS
    AWS_REGION = os.getenv("AWS_REGION")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

    # Google
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL_ID = os.getenv("GOOGLE_MODEL_ID", "gemini-pro")

    # Grok (generic HTTP-based integration)
    GROK_API_KEY = os.getenv("GROK_API_KEY")
    GROK_API_URL = os.getenv("GROK_API_URL")
    GROK_MODEL_ID = os.getenv("GROK_MODEL_ID")

    # API token for simple bearer auth used in Swagger / API access
    API_TOKEN = os.getenv("API_TOKEN")


settings = Settings()