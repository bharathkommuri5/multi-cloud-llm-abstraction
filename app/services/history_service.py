from uuid import UUID
from sqlalchemy.orm import Session
from app.models.llm_call_history import LLMCallHistory
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class HistoryService:
    """Service layer for LLM call history operations"""

    @staticmethod
    def get_user_history(
        user_id: UUID,
        db: Session,
        limit: int = 50,
        offset: int = 0
    ) -> list[LLMCallHistory]:
        """Get LLM call history for a user (excludes soft-deleted records)"""
        # Verify user exists and is not deleted
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        if not user:
            raise ValueError("User not found or has been deleted")
        
        history = db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user_id,
            LLMCallHistory.deleted_at == None
        ).order_by(
            LLMCallHistory.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return history

    @staticmethod
    def get_history_detail(history_id: int, db: Session) -> LLMCallHistory:
        """Get details of a specific call (excludes soft-deleted records)"""
        history = db.query(LLMCallHistory).filter(
            LLMCallHistory.id == history_id,
            LLMCallHistory.deleted_at == None
        ).first()
        
        if not history:
            raise ValueError("History record not found")
        
        return history

    @staticmethod
    def log_call(
        user_id: UUID,
        provider_id: int,
        model_id: int,
        prompt: str,
        response: str,
        parameters_used: dict,
        status: str = "success",
        error_message: str = None,
        tokens_input: int = None,
        tokens_output: int = None,
        total_tokens: int = None,
        cost: float = None,
        db: Session = None
    ) -> LLMCallHistory:
        """Log an LLM call to history"""
        logger.info(f"Logging call for user {user_id}, provider {provider_id}")
        
        history_record = LLMCallHistory(
            user_id=user_id,
            provider_id=provider_id,
            model_id=model_id,
            prompt=prompt,
            response=response,
            parameters_used=parameters_used,
            status=status,
            error_message=error_message,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            total_tokens=total_tokens,
            cost=cost,
        )
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        
        return history_record

    @staticmethod
    def get_user_stats(user_id: UUID, db: Session) -> dict:
        """Get usage statistics for a user"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        if not user:
            raise ValueError("User not found or has been deleted")
        
        total_calls = db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user_id,
            LLMCallHistory.deleted_at == None,
            LLMCallHistory.status == "success"
        ).count()
        
        failed_calls = db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user_id,
            LLMCallHistory.deleted_at == None,
            LLMCallHistory.status == "error"
        ).count()
        
        total_tokens = db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user_id,
            LLMCallHistory.deleted_at == None,
            LLMCallHistory.status == "success"
        ).with_entities(
            db.func.sum(LLMCallHistory.total_tokens).label("total")
        ).scalar() or 0
        
        total_cost = db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user_id,
            LLMCallHistory.deleted_at == None,
            LLMCallHistory.status == "success"
        ).with_entities(
            db.func.sum(LLMCallHistory.cost).label("total")
        ).scalar() or 0.0
        
        return {
            "total_calls": total_calls,
            "failed_calls": failed_calls,
            "total_tokens": int(total_tokens),
            "total_cost": float(total_cost),
            "success_rate": (
                (total_calls / (total_calls + failed_calls) * 100) 
                if (total_calls + failed_calls) > 0 else 0
            )
        }
