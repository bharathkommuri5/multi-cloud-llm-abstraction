from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.history import LLMCallHistoryResponse
from app.services.history_service import HistoryService
from app.api.v1.dependencies import parse_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[LLMCallHistoryResponse])
def get_user_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get LLM call history for a user
    
    - user_id: UUID of the user
    - limit: Number of records to return (default: 50)
    - offset: Number of records to skip (default: 0)
    """
    user_uuid = parse_user_id(user_id)
    
    try:
        history = HistoryService.get_user_history(
            user_uuid,
            db,
            limit=limit,
            offset=offset
        )
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{history_id}", response_model=LLMCallHistoryResponse)
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    """Get details of a specific call"""
    try:
        history = HistoryService.get_history_detail(history_id, db)
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/user/{user_id}/stats")
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """
    Get usage statistics for a user
    
    Returns:
    - total_calls: Number of successful calls
    - failed_calls: Number of failed calls
    - total_tokens: Total tokens used
    - total_cost: Total cost incurred
    - success_rate: Percentage of successful calls
    """
    user_uuid = parse_user_id(user_id)
    
    try:
        stats = HistoryService.get_user_stats(user_uuid, db)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
