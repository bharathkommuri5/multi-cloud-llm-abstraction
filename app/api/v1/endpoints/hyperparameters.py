from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.hyperparameter import (
    HyperparameterConfigCreate,
    HyperparameterConfigResponse,
    HyperparameterConfigUpdate
)
from app.services.hyperparameter_service import HyperparameterService
from app.api.v1.dependencies import parse_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hyperparameters", tags=["hyperparameters"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{user_id}", response_model=HyperparameterConfigResponse, status_code=201)
def create_config(
    user_id: str,
    config_data: HyperparameterConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Create a hyperparameter configuration for a user-model combo
    
    - user_id: UUID of the user
    - model_id: ID of the LLM model
    - parameters: Dict of hyperparameters (e.g., {"temperature": 0.7, "top_p": 0.9})
    - description: Optional description of this config
    - is_default: Mark this as the default config for this model
    """
    user_uuid = parse_user_id(user_id)
    
    try:
        config = HyperparameterService.create_config(user_uuid, config_data, db)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=list[HyperparameterConfigResponse])
def list_configs(user_id: str, db: Session = Depends(get_db)):
    """Get all active hyperparameter configs for a user"""
    user_uuid = parse_user_id(user_id)
    
    try:
        configs = HyperparameterService.get_user_configs(user_uuid, db)
        return configs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{user_id}/{config_id}", response_model=HyperparameterConfigResponse)
def get_config(user_id: str, config_id: int, db: Session = Depends(get_db)):
    """Get a specific hyperparameter config"""
    user_uuid = parse_user_id(user_id)
    
    try:
        config = HyperparameterService.get_config(user_uuid, config_id, db)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{user_id}/{config_id}", response_model=HyperparameterConfigResponse)
def update_config(
    user_id: str,
    config_id: int,
    config_data: HyperparameterConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a hyperparameter config"""
    user_uuid = parse_user_id(user_id)
    
    try:
        config = HyperparameterService.update_config(user_uuid, config_id, config_data, db)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{user_id}/{config_id}", status_code=200)
def delete_config(user_id: str, config_id: int, db: Session = Depends(get_db)):
    """Soft delete a hyperparameter config"""
    user_uuid = parse_user_id(user_id)
    
    try:
        result = HyperparameterService.delete_config(user_uuid, config_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
