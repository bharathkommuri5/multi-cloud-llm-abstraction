from uuid import UUID
from sqlalchemy.orm import Session
from app.models.provider import Provider
from app.models.llm_model import LLMModel
from app.models.hyperparameter_config import HyperparameterConfig
from app.models.user import User
from app.llm.factory import get_llm_client
from app.core.exceptions import LLMProviderError
from app.services.history_service import HistoryService
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service layer for LLM operations"""

    @staticmethod
    def apply_hyperparameter_config(config: HyperparameterConfig, custom_params: dict = None) -> dict:
        """Merge hyperparameter config with custom parameters"""
        params = config.parameters.copy() if config.parameters else {}
        
        # Override with custom parameters if provided
        if custom_params:
            params.update(custom_params)
        
        return params

    @staticmethod
    def get_llm_parameters(
        user_id: UUID,
        model_id: int,
        temperature: float = 0.7,
        max_tokens: int = 300,
        hyperparameter_config_id: int = None,
        custom_parameters: dict = None,
        db: Session = None
    ) -> dict:
        """Determine which parameters to use for LLM call"""
        parameters_to_use = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # If hyperparameter config is specified, use it
        if hyperparameter_config_id:
            config = db.query(HyperparameterConfig).filter(
                HyperparameterConfig.id == hyperparameter_config_id,
                HyperparameterConfig.user_id == user_id,
                HyperparameterConfig.model_id == model_id,
                HyperparameterConfig.deleted_at == None
            ).first()
            
            if config:
                parameters_to_use = LLMService.apply_hyperparameter_config(config, custom_parameters)
        elif custom_parameters:
            # Override with custom parameters
            parameters_to_use.update(custom_parameters)
        
        return parameters_to_use

    @staticmethod
    def generate_response(
        user_id: UUID,
        provider_name: str,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        hyperparameter_config_id: int = None,
        custom_parameters: dict = None,
        db: Session = None
    ) -> dict:
        """Generate a response from LLM and log the call"""
        logger.info(f"Generating response for user {user_id}, model {model_name}")
        
        # Verify user exists and is not deleted
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        if not user:
            raise ValueError("User not found or has been deleted")
        
        # Get provider
        provider = db.query(Provider).filter(Provider.name == provider_name).first()
        if not provider:
            raise ValueError("Provider not found")

        # Get model
        model = db.query(LLMModel).filter(
            LLMModel.name == model_name,
            LLMModel.provider_id == provider.id
        ).first()

        if not model:
            raise ValueError("Model not found for provider")

        # Determine parameters to use
        parameters_to_use = LLMService.get_llm_parameters(
            user_id=user_id,
            model_id=model.id,
            temperature=temperature,
            max_tokens=max_tokens,
            hyperparameter_config_id=hyperparameter_config_id,
            custom_parameters=custom_parameters,
            db=db
        )

        # Call LLM
        client = get_llm_client(provider.type)
        
        try:
            result = client.generate(
                prompt=prompt,
                temperature=parameters_to_use.get("temperature", 0.7),
                max_tokens=parameters_to_use.get("max_tokens", 300),
            )
            
            status = "success"
            error_message = None
            
        except LLMProviderError as e:
            status = "error"
            error_message = str(e)
            result = None
            logger.error(f"LLM Provider Error for user {user_id}: {error_message}")
            raise ValueError(f"LLM Error: {error_message}")
        except Exception as e:
            status = "error"
            error_message = str(e)
            result = None
            logger.error(f"Unexpected error for user {user_id}: {error_message}")
            raise ValueError("Internal server error")
        
        finally:
            # Log the call regardless of success or failure
            history_record = HistoryService.log_call(
                user_id=user_id,
                provider_id=provider.id,
                model_id=model.id,
                prompt=prompt,
                response=result or "",
                parameters_used=parameters_to_use,
                status=status,
                error_message=error_message,
                db=db
            )

        return {
            "provider": provider_name,
            "model": model_name,
            "response": result,
            "history_id": history_record.id
        }
