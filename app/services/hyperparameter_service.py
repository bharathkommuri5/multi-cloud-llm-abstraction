from uuid import UUID
from sqlalchemy.orm import Session
from app.models.hyperparameter_config import HyperparameterConfig
from app.models.llm_model import LLMModel
from app.models.user import User
from app.schemas.hyperparameter import HyperparameterConfigCreate, HyperparameterConfigUpdate
import logging

logger = logging.getLogger(__name__)


class HyperparameterService:
    """Service layer for hyperparameter configuration operations"""

    @staticmethod
    def create_config(
        user_id: UUID,
        config_data: HyperparameterConfigCreate,
        db: Session
    ) -> HyperparameterConfig:
        """Create a hyperparameter configuration for a user-model combo"""
        logger.info(f"Creating hyperparameter config for user {user_id}, model {config_data.model_id}")
        
        # Verify user exists and is not deleted
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        if not user:
            raise ValueError("User not found or has been deleted")
        
        # Verify model exists
        model = db.query(LLMModel).filter(LLMModel.id == config_data.model_id).first()
        if not model:
            raise ValueError("Model not found")
        
        # If marking as default, unmark other defaults for this user-model
        if config_data.is_default:
            db.query(HyperparameterConfig).filter(
                HyperparameterConfig.user_id == user_id,
                HyperparameterConfig.model_id == config_data.model_id,
                HyperparameterConfig.is_default == True,
                HyperparameterConfig.deleted_at == None
            ).update({"is_default": False}, synchronize_session=False)
        
        config = HyperparameterConfig(
            user_id=user_id,
            model_id=config_data.model_id,
            parameters=config_data.parameters,
            description=config_data.description,
            is_default=config_data.is_default
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def get_user_configs(user_id: UUID, db: Session) -> list[HyperparameterConfig]:
        """Get all active hyperparameter configs for a user"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        if not user:
            raise ValueError("User not found or has been deleted")
        
        configs = db.query(HyperparameterConfig).filter(
            HyperparameterConfig.user_id == user_id,
            HyperparameterConfig.deleted_at == None
        ).all()
        return configs

    @staticmethod
    def get_config(user_id: UUID, config_id: int, db: Session) -> HyperparameterConfig:
        """Get a specific hyperparameter config"""
        config = db.query(HyperparameterConfig).filter(
            HyperparameterConfig.id == config_id,
            HyperparameterConfig.user_id == user_id,
            HyperparameterConfig.deleted_at == None
        ).first()
        
        if not config:
            raise ValueError("Config not found")
        return config

    @staticmethod
    def update_config(
        user_id: UUID,
        config_id: int,
        config_data: HyperparameterConfigUpdate,
        db: Session
    ) -> HyperparameterConfig:
        """Update a hyperparameter config"""
        config = db.query(HyperparameterConfig).filter(
            HyperparameterConfig.id == config_id,
            HyperparameterConfig.user_id == user_id,
            HyperparameterConfig.deleted_at == None
        ).first()
        
        if not config:
            raise ValueError("Config not found")
        
        if config_data.parameters:
            config.parameters = config_data.parameters
        if config_data.description is not None:
            config.description = config_data.description
        if config_data.is_default is not None:
            if config_data.is_default:
                # Unmark other defaults
                db.query(HyperparameterConfig).filter(
                    HyperparameterConfig.user_id == user_id,
                    HyperparameterConfig.model_id == config.model_id,
                    HyperparameterConfig.is_default == True,
                    HyperparameterConfig.id != config_id,
                    HyperparameterConfig.deleted_at == None
                ).update({"is_default": False}, synchronize_session=False)
            config.is_default = config_data.is_default
        
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def delete_config(user_id: UUID, config_id: int, db: Session) -> dict:
        """Soft delete a hyperparameter config"""
        from datetime import datetime
        
        config = db.query(HyperparameterConfig).filter(
            HyperparameterConfig.id == config_id,
            HyperparameterConfig.user_id == user_id,
            HyperparameterConfig.deleted_at == None
        ).first()
        
        if not config:
            raise ValueError("Config not found")
        
        logger.info(f"Deleting config {config_id} for user {user_id}")
        config.deleted_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Config soft deleted"}
