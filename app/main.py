from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.database import Base, engine
from app.core.middleware import CorrelationIdMiddleware
from app.core.auth_middleware import AuthMiddleware
from app.utils.logger import config_logger as logger
from app.core.config import settings
from app.api import api_router
# Import all models to register them with SQLAlchemy
from app.models import Provider, LLMModel, User, HyperparameterConfig, LLMCallHistory

Base.metadata.create_all(bind=engine)
logger.info("Database tables created/verified")

# Log config initialization status
logger.info(f"Settings initialized | JWT_ALG: {settings.JWT_ALG} | Token expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} min")
if not settings.JWT_SECRET:
    logger.warning("JWT_SECRET not configured - token issuance will fail")
if not settings.GOOGLE_CLIENT_ID:
    logger.warning("GOOGLE_CLIENT_ID not configured - Google sign-in will fail")
if not settings.API_TOKEN:
    logger.warning("API_TOKEN not configured - API authorization may not work")

app = FastAPI(
    title="Multi-Cloud LLM Gateway API",
    description="Unified abstraction layer for Azure OpenAI, AWS Bedrock, Google Generative AI, and Grok",
    version="1.0.0"
)
logger.info("FastAPI application initialized")

templates = Jinja2Templates(directory="app/templates")
logger.info("Templates directory initialized")

# Add middleware in reverse order (last added = first executed)
app.add_middleware(AuthMiddleware)
logger.info("Auth middleware registered - validates JWT tokens on protected routes")

app.add_middleware(CorrelationIdMiddleware)
logger.info("Correlation ID middleware registered")

# Include API v1 routes
app.include_router(api_router)
logger.info("API routes registered")


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
