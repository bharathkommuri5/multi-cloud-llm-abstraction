from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Multi-Cloud LLM Abstraction Service",
    version="1.0.0"
)

app.include_router(router, prefix="/api")
