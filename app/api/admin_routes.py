from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.schemas.provider import ProviderCreate, ProviderResponse
from app.schemas.model import ModelCreate, ModelResponse
import logging

logger = logging.getLogger(__name__)

admin_router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@admin_router.post("/providers")
def create_provider(data: ProviderCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating provider: {data.name}")
    provider = Provider(name=data.name, type=data.type)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@admin_router.post("/models")
def create_model(data: ModelCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating model: {data.name}")
    model = LLMModel(name=data.name, provider_id=data.provider_id)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

@admin_router.get("/providers", response_model=list[ProviderResponse])
def get_providers(db: Session = Depends(get_db)):
    logger.info("Retrieving active providers")
    providers = db.query(Provider).filter(Provider.is_active == True).all()
    return providers

@admin_router.get("/models", response_model=list[ModelResponse])
def get_models(db: Session = Depends(get_db)):
    logger.info("Retrieving active models")
    models = db.query(LLMModel).filter(LLMModel.is_active == True).all()
    return models


@admin_router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete provider with ID: {provider_id}")
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

        return {
            "message": "Provider and associated models soft deleted successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete model with ID: {model_id}")
    model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_active == True
    ).first()

    if not model:
        return {"message": "Model not found"}

    model.is_active = False
    db.commit()

    return {"message": "Model soft deleted"}
