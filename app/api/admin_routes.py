from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.models.user import User
from app.models.hyperparameter_config import HyperparameterConfig
from app.schemas.provider import ProviderCreate, ProviderResponse
from app.schemas.model import ModelCreate, ModelResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserDeletionPreview, UserRestoreRequest
from app.schemas.hyperparameter import HyperparameterConfigCreate, HyperparameterConfigResponse, HyperparameterConfigUpdate
from app.core.deletion_service import get_deletion_preview, soft_delete_user, restore_user, hard_delete_expired_users, get_soft_deleted_users
from uuid import UUID
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


# ============= USER ENDPOINTS =============

@admin_router.post("/users", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    logger.info(f"Creating user: {data.username}")
    
    # Check if user already exists
    existing = db.query(User).filter(
        (User.username == data.username) | (User.email == data.email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = User(username=data.username, email=data.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@admin_router.get("/users", response_model=list[UserResponse])
def get_users(include_deleted: bool = False, db: Session = Depends(get_db)):
    """Get all active users (optionally include deleted ones)"""
    logger.info(f"Retrieving users (include_deleted={include_deleted})")
    
    if include_deleted:
        users = db.query(User).all()
    else:
        users = db.query(User).filter(User.deleted_at == None).all()
    
    return users


@admin_router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@admin_router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, data: UserUpdate, db: Session = Depends(get_db)):
    """Update user details (only non-deleted users)"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or has been deleted")
    
    if data.username:
        user.username = data.username
    if data.email:
        user.email = data.email
    
    db.commit()
    db.refresh(user)
    return user


# ============= USER DELETION ENDPOINTS =============

@admin_router.get("/users/{user_id}/deletion-preview", response_model=UserDeletionPreview)
def preview_user_deletion(user_id: str, db: Session = Depends(get_db)):
    """Preview what will be deleted when user is soft-deleted"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    preview = get_deletion_preview(user_uuid, db)
    
    if not preview:
        raise HTTPException(status_code=404, detail="User not found")
    
    return preview


@admin_router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Soft delete a user and all their associated data"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Soft deleting user: {user_uuid}")
    result = soft_delete_user(user_uuid, db)
    
    return result


@admin_router.post("/users/{user_id}/restore")
def restore_deleted_user(user_id: str, db: Session = Depends(get_db)):
    """Restore a soft-deleted user and their data (within 7-day recovery window)"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    logger.info(f"Restoring user: {user_uuid}")
    result = restore_user(user_uuid, db)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@admin_router.get("/users/deleted/list")
def list_deleted_users(db: Session = Depends(get_db)):
    """List all soft-deleted users with their recovery deadline"""
    logger.info("Listing soft-deleted users")
    deleted_users = get_soft_deleted_users(db)
    
    return {
        "total": len(deleted_users),
        "users": deleted_users
    }


@admin_router.post("/maintenance/hard-delete-expired")
def trigger_hard_delete(db: Session = Depends(get_db)):
    """
    Permanently delete users who exceeded the 7-day recovery window.
    This endpoint should be called periodically (e.g., daily via cron job).
    """
    logger.warning("Triggering hard delete for expired soft-deleted users")
    result = hard_delete_expired_users(db)
    
    return result


# ============= HYPERPARAMETER CONFIG ENDPOINTS =============

@admin_router.post("/users/{user_id}/hyperparameters", response_model=HyperparameterConfigResponse)
def create_hyperparameter_config(
    user_id: str,
    data: HyperparameterConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a hyperparameter configuration for a user-model combo"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    logger.info(f"Creating hyperparameter config for user {user_id}, model {data.model_id}")
    
    # Verify user exists and is not deleted
    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or has been deleted")
    
    # Verify model exists
    model = db.query(LLMModel).filter(LLMModel.id == data.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # If marking as default, unmark other defaults for this user-model
    if data.is_default:
        db.query(HyperparameterConfig).filter(
            HyperparameterConfig.user_id == user_uuid,
            HyperparameterConfig.model_id == data.model_id,
            HyperparameterConfig.is_default == True,
            HyperparameterConfig.deleted_at == None
        ).update({"is_default": False}, synchronize_session=False)
    
    config = HyperparameterConfig(
        user_id=user_uuid,
        model_id=data.model_id,
        parameters=data.parameters,
        description=data.description,
        is_default=data.is_default
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@admin_router.get("/users/{user_id}/hyperparameters", response_model=list[HyperparameterConfigResponse])
def get_user_hyperparameter_configs(user_id: str, db: Session = Depends(get_db)):
    """Get all active hyperparameter configs for a user"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or has been deleted")
    
    configs = db.query(HyperparameterConfig).filter(
        HyperparameterConfig.user_id == user_uuid,
        HyperparameterConfig.deleted_at == None
    ).all()
    return configs


@admin_router.get("/users/{user_id}/hyperparameters/{config_id}", response_model=HyperparameterConfigResponse)
def get_hyperparameter_config(user_id: str, config_id: int, db: Session = Depends(get_db)):
    """Get a specific hyperparameter config"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    config = db.query(HyperparameterConfig).filter(
        HyperparameterConfig.id == config_id,
        HyperparameterConfig.user_id == user_uuid,
        HyperparameterConfig.deleted_at == None
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@admin_router.put("/users/{user_id}/hyperparameters/{config_id}", response_model=HyperparameterConfigResponse)
def update_hyperparameter_config(
    user_id: str,
    config_id: int,
    data: HyperparameterConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a hyperparameter config"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    config = db.query(HyperparameterConfig).filter(
        HyperparameterConfig.id == config_id,
        HyperparameterConfig.user_id == user_uuid,
        HyperparameterConfig.deleted_at == None
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    if data.parameters:
        config.parameters = data.parameters
    if data.description is not None:
        config.description = data.description
    if data.is_default is not None:
        if data.is_default:
            # Unmark other defaults
            db.query(HyperparameterConfig).filter(
                HyperparameterConfig.user_id == user_uuid,
                HyperparameterConfig.model_id == config.model_id,
                HyperparameterConfig.is_default == True,
                HyperparameterConfig.id != config_id,
                HyperparameterConfig.deleted_at == None
            ).update({"is_default": False}, synchronize_session=False)
        config.is_default = data.is_default
    
    db.commit()
    db.refresh(config)
    return config


@admin_router.delete("/users/{user_id}/hyperparameters/{config_id}")
def delete_hyperparameter_config(user_id: str, config_id: int, db: Session = Depends(get_db)):
    """Soft delete a hyperparameter config"""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    config = db.query(HyperparameterConfig).filter(
        HyperparameterConfig.id == config_id,
        HyperparameterConfig.user_id == user_uuid,
        HyperparameterConfig.deleted_at == None
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    from datetime import datetime
    config.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Config soft deleted"}
