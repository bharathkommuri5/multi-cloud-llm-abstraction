from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.request import LLMRequest
from app.schemas.response import LLMResponse
from app.services.llm_service import LLMService
from app.api.v1.dependencies import parse_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate", response_model=LLMResponse)
def generate_text(request: LLMRequest, req: Request, db: Session = Depends(get_db)):
    """
    Generate text using an LLM
    
    - user_id: UUID of the user making the request
    - provider: Name of the LLM provider (azure, bedrock, google)
    - model: Model name
    - prompt: The prompt to send to the LLM
    - temperature: Sampling temperature (0-1)
    - max_tokens: Maximum tokens in response
    - hyperparameter_config_id: Optional config ID to use saved parameters
    - custom_parameters: Optional dict to override specific parameters
    """
    correlation_id = req.state.correlation_id
    user_uuid = parse_user_id(str(request.user_id))
    
    logger.info(f"[{correlation_id}] Generate API called by user {user_uuid}")
    
    try:
        result = LLMService.generate_response(
            user_id=user_uuid,
            provider_name=request.provider,
            model_name=request.model,
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            hyperparameter_config_id=request.hyperparameter_config_id,
            custom_parameters=request.custom_parameters,
            db=db
        )
        
        return LLMResponse(**result)
        
    except ValueError as e:
        logger.error(f"[{correlation_id}] {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
