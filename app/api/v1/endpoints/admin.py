from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.schemas.provider import ProviderCreate, ProviderResponse
from app.schemas.model import ModelCreate, ModelResponse
from app.services.deletion_service import DeletionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============= PROVIDER ENDPOINTS =============

@router.post("/providers", response_model=ProviderResponse, status_code=201)
def create_provider(data: ProviderCreate, db: Session = Depends(get_db)):
    """Create a new LLM provider"""
    logger.info(f"Creating provider: {data.name}")
    provider = Provider(name=data.name, type=data.type)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/providers", response_model=list[ProviderResponse])
def list_providers(db: Session = Depends(get_db)):
    """Get all active providers"""
    providers = db.query(Provider).filter(Provider.is_active == True).all()
    return providers


@router.delete("/providers/{provider_id}", status_code=200)
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    """Soft delete a provider and its models"""
    logger.info(f"Deleting provider with ID: {provider_id}")
    provider = db.query(Provider).filter(
        Provider.id == provider_id,
        Provider.is_active == True
    ).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        # Soft delete all models under this provider
        db.query(LLMModel).filter(
            LLMModel.provider_id == provider_id,
            LLMModel.is_active == True
        ).update(
            {"is_active": False},
            synchronize_session=False
        )

        # Soft delete provider
        provider.is_active = False
        db.commit()

        return {"message": "Provider and associated models soft deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============= MODEL ENDPOINTS =============

@router.post("/models", response_model=ModelResponse, status_code=201)
def create_model(data: ModelCreate, db: Session = Depends(get_db)):
    """Create a new LLM model"""
    logger.info(f"Creating model: {data.name}")
    model = LLMModel(name=data.name, provider_id=data.provider_id)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/models", response_model=list[ModelResponse])
def list_models(db: Session = Depends(get_db)):
    """Get all active models"""
    models = db.query(LLMModel).filter(LLMModel.is_active == True).all()
    return models


@router.delete("/models/{model_id}", status_code=200)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Soft delete a model"""
    logger.info(f"Deleting model with ID: {model_id}")
    model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_active == True
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model.is_active = False
    db.commit()
    return {"message": "Model soft deleted"}


# ============= MAINTENANCE ENDPOINTS =============

@router.get("/deleted-users")
def list_deleted_users(db: Session = Depends(get_db)):
    """List all soft-deleted users with their recovery deadline"""
    logger.info("Listing soft-deleted users")
    deleted_users = DeletionService.get_soft_deleted_users(db)
    
    return {
        "total": len(deleted_users),
        "users": deleted_users
    }


@router.post("/hard-delete-expired", status_code=200)
def trigger_hard_delete(db: Session = Depends(get_db)):
    """
    Permanently delete users who exceeded the 7-day recovery window.
    Should be called periodically (e.g., daily via cron job).
    """
    logger.warning("Triggering hard delete for expired soft-deleted users")
    result = DeletionService.hard_delete_expired_users(db)
    
    return result
