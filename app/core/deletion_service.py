"""
Utility functions for handling soft deletes and data cleanup
"""
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User
from app.models.llm_call_history import LLMCallHistory
from app.models.hyperparameter_config import HyperparameterConfig
from app.schemas.user import UserDeletionPreview


SOFT_DELETE_RETENTION_DAYS = 7


def get_deletion_preview(user_id: UUID, db: Session) -> UserDeletionPreview:
    """Get a preview of what will be deleted when user is soft-deleted"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return None
    
    # Count related records
    call_history_count = db.query(LLMCallHistory).filter(
        LLMCallHistory.user_id == user_id,
        LLMCallHistory.deleted_at == None
    ).count()
    
    config_count = db.query(HyperparameterConfig).filter(
        HyperparameterConfig.user_id == user_id,
        HyperparameterConfig.deleted_at == None
    ).count()
    
    recovery_deadline = datetime.utcnow() + timedelta(days=SOFT_DELETE_RETENTION_DAYS)
    
    message = (
        f"User '{user.username}' will be deleted along with:\n"
        f"- {call_history_count} LLM call history records\n"
        f"- {config_count} hyperparameter configurations\n\n"
        f"The data will be retained for {SOFT_DELETE_RETENTION_DAYS} days "
        f"and can be restored until {recovery_deadline.strftime('%Y-%m-%d %H:%M:%S')} UTC.\n"
        f"After this period, all data will be permanently deleted."
    )
    
    return UserDeletionPreview(
        user_id=user.id,
        username=user.username,
        email=user.email,
        total_call_history_records=call_history_count,
        total_hyperparameter_configs=config_count,
        recovery_deadline=recovery_deadline,
        message=message
    )


def soft_delete_user(user_id: UUID, db: Session) -> dict:
    """Soft delete a user and their associated data"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return None
    
    now = datetime.utcnow()
    
    # Soft delete user
    user.deleted_at = now
    user.is_active = False
    
    # Soft delete all call history records for this user
    db.query(LLMCallHistory).filter(
        LLMCallHistory.user_id == user_id,
        LLMCallHistory.deleted_at == None
    ).update({"deleted_at": now}, synchronize_session=False)
    
    # Soft delete all hyperparameter configs for this user
    db.query(HyperparameterConfig).filter(
        HyperparameterConfig.user_id == user_id,
        HyperparameterConfig.deleted_at == None
    ).update({"deleted_at": now}, synchronize_session=False)
    
    db.commit()
    
    return {
        "message": "User soft deleted successfully",
        "user_id": str(user_id),
        "deleted_at": now.isoformat(),
        "recovery_deadline": (now + timedelta(days=SOFT_DELETE_RETENTION_DAYS)).isoformat()
    }


def restore_user(user_id: UUID, db: Session) -> dict:
    """Restore a soft-deleted user and their data"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return None
    
    if user.deleted_at is None:
        return {
            "error": "User is not soft-deleted",
            "user_id": str(user_id)
        }
    
    # Check if within recovery window
    recovery_deadline = user.deleted_at + timedelta(days=SOFT_DELETE_RETENTION_DAYS)
    if datetime.utcnow() > recovery_deadline:
        return {
            "error": f"Recovery window has expired. Data was permanently deleted on {recovery_deadline.isoformat()}",
            "user_id": str(user_id)
        }
    
    # Restore user
    user.deleted_at = None
    user.is_active = True
    
    # Restore all call history records
    db.query(LLMCallHistory).filter(
        LLMCallHistory.user_id == user_id,
        LLMCallHistory.deleted_at != None
    ).update({"deleted_at": None}, synchronize_session=False)
    
    # Restore all hyperparameter configs
    db.query(HyperparameterConfig).filter(
        HyperparameterConfig.user_id == user_id,
        HyperparameterConfig.deleted_at != None
    ).update({"deleted_at": None}, synchronize_session=False)
    
    db.commit()
    
    return {
        "message": "User and associated data restored successfully",
        "user_id": str(user_id),
        "restored_at": datetime.utcnow().isoformat()
    }


def hard_delete_expired_users(db: Session) -> dict:
    """
    Permanently delete users who have been soft-deleted for more than 7 days.
    This should be called periodically (e.g., via a cron job or background task).
    """
    cutoff_date = datetime.utcnow() - timedelta(days=SOFT_DELETE_RETENTION_DAYS)
    
    # Find users who have been soft-deleted beyond the retention period
    expired_users = db.query(User).filter(
        and_(
            User.deleted_at != None,
            User.deleted_at < cutoff_date
        )
    ).all()
    
    deleted_count = 0
    deleted_user_ids = []
    
    for user in expired_users:
        # Delete call history records
        db.query(LLMCallHistory).filter(
            LLMCallHistory.user_id == user.id
        ).delete(synchronize_session=False)
        
        # Delete hyperparameter configs
        db.query(HyperparameterConfig).filter(
            HyperparameterConfig.user_id == user.id
        ).delete(synchronize_session=False)
        
        # Delete user
        db.delete(user)
        deleted_count += 1
        deleted_user_ids.append(str(user.id))
    
    db.commit()
    
    return {
        "message": f"Hard deleted {deleted_count} expired users",
        "deleted_count": deleted_count,
        "deleted_user_ids": deleted_user_ids,
        "cutoff_date": cutoff_date.isoformat()
    }


def get_soft_deleted_users(db: Session) -> list:
    """Get all soft-deleted users and their recovery deadlines"""
    deleted_users = db.query(User).filter(User.deleted_at != None).all()
    
    result = []
    for user in deleted_users:
        recovery_deadline = user.deleted_at + timedelta(days=SOFT_DELETE_RETENTION_DAYS)
        is_expired = datetime.utcnow() > recovery_deadline
        
        result.append({
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "deleted_at": user.deleted_at.isoformat(),
            "recovery_deadline": recovery_deadline.isoformat(),
            "is_expired": is_expired
        })
    
    return result
