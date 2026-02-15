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


settings = Settings()