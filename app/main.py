from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.database import Base, engine
from app.core.middleware import CorrelationIdMiddleware
from app.api import api_router
# Import all models to register them with SQLAlchemy
from app.models import Provider, LLMModel, User, HyperparameterConfig, LLMCallHistory

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Cloud LLM Gateway API",
    description="Unified abstraction layer for Azure OpenAI, AWS Bedrock, and Google Generative AI",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(CorrelationIdMiddleware)

# Include API v1 routes
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
