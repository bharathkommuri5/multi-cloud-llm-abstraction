from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.models.llm_call_history import LLMCallHistory
from app.models.hyperparameter_config import HyperparameterConfig
from app.models.user import User
from app.schemas.request import LLMRequest
from app.schemas.response import LLMResponse
from app.schemas.history import LLMCallHistoryResponse
from app.llm.factory import get_llm_client
from app.core.exceptions import LLMProviderError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_hyperparameter_config(config: HyperparameterConfig, request: LLMRequest):
    """Merge hyperparameter config with request params"""
    params = config.parameters.copy() if config.parameters else {}
    
    # Override with custom parameters if provided
    if request.custom_parameters:
        params.update(request.custom_parameters)
    
    return params


@router.post("/generate", response_model=LLMResponse)
def generate_text(request: LLMRequest, req: Request, db: Session = Depends(get_db)):
    correlation_id = req.state.correlation_id
    logger.info(f"[{correlation_id}] Generate API called by user {request.user_id}")
    
    # Verify user exists and is not deleted
    user = db.query(User).filter(
        User.id == request.user_id,
        User.deleted_at == None
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or has been deleted")
    
    # Get provider
    provider = db.query(Provider).filter(Provider.name == request.provider).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Get model
    model = db.query(LLMModel).filter(
        LLMModel.name == request.model,
        LLMModel.provider_id == provider.id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found for provider")

    # Determine parameters to use
    parameters_to_use = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    
    # If hyperparameter config is specified, use it
    if request.hyperparameter_config_id:
        config = db.query(HyperparameterConfig).filter(
            HyperparameterConfig.id == request.hyperparameter_config_id,
            HyperparameterConfig.user_id == request.user_id,
            HyperparameterConfig.model_id == model.id,
            HyperparameterConfig.deleted_at == None
        ).first()
        
        if config:
            parameters_to_use = apply_hyperparameter_config(config, request)
    elif request.custom_parameters:
        # Override with custom parameters
        parameters_to_use.update(request.custom_parameters)

    # Call LLM
    client = get_llm_client(provider.type)
    
    history_record = None
    try:
        result = client.generate(
            prompt=request.prompt,
            temperature=parameters_to_use.get("temperature", 0.7),
            max_tokens=parameters_to_use.get("max_tokens", 300),
        )
        
        status = "success"
        error_message = None
        
    except LLMProviderError as e:
        status = "error"
        error_message = str(e)
        result = None
        logger.error(f"[{correlation_id}] LLM Provider Error: {error_message}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        status = "error"
        error_message = str(e)
        result = None
        logger.error(f"[{correlation_id}] Unexpected error: {error_message}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        # Log the call regardless of success or failure
        history_record = LLMCallHistory(
            user_id=request.user_id,
            provider_id=provider.id,
            model_id=model.id,
            prompt=request.prompt,
            response=result or "",
            parameters_used=parameters_to_use,
            status=status,
            error_message=error_message,
        )
        db.add(history_record)
        db.commit()
        logger.info(f"[{correlation_id}] Call logged to history (ID: {history_record.id})")

    return LLMResponse(
        provider=request.provider,
        model=request.model,
        response=result,
        history_id=history_record.id
    )


@router.get("/history", response_model=list[LLMCallHistoryResponse])
def get_user_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get LLM call history for a user (excludes soft-deleted records)"""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Verify user exists and is not deleted
    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or has been deleted")
    
    history = db.query(LLMCallHistory).filter(
        LLMCallHistory.user_id == user_uuid,
        LLMCallHistory.deleted_at == None
    ).order_by(
        LLMCallHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return history


@router.get("/history/{history_id}", response_model=LLMCallHistoryResponse)
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    """Get details of a specific call (excludes soft-deleted records)"""
    history = db.query(LLMCallHistory).filter(
        LLMCallHistory.id == history_id,
        LLMCallHistory.deleted_at == None
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="History record not found")
    
    return history

