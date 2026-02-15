from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.schemas.request import LLMRequest
from app.schemas.response import LLMResponse
from app.llm.factory import get_llm_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate", response_model=LLMResponse)
def generate_text(request: LLMRequest, req: Request, db: Session = Depends(get_db)):
    correlation_id = req.state.correlation_id
    logger.info(f"[{correlation_id}] Generate API called")
    provider = db.query(Provider).filter(Provider.name == request.provider).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model = db.query(LLMModel).filter(
        LLMModel.name == request.model,
        LLMModel.provider_id == provider.id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found for provider")

    client = get_llm_client(provider.type)

    result = client.generate(
        model=request.model,
        prompt=request.prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return LLMResponse(provider=request.provider, response=result)
