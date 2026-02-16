from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserDeletionPreview
from app.services.user_service import UserService
from app.services.deletion_service import DeletionService
from app.api.v1.dependencies import parse_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        user = UserService.create_user(user_data, db)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[UserResponse])
def list_users(include_deleted: bool = False, db: Session = Depends(get_db)):
    """Get all users"""
    users = UserService.get_all_users(db, include_deleted=include_deleted)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user"""
    user_uuid = parse_user_id(user_id)
    user = UserService.get_user(user_uuid, db)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Update user details"""
    user_uuid = parse_user_id(user_id)
    
    try:
        user = UserService.update_user(user_uuid, user_data, db)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{user_id}/deletion-preview", response_model=UserDeletionPreview)
def preview_deletion(user_id: str, db: Session = Depends(get_db)):
    """Preview what will be deleted when user is soft-deleted"""
    user_uuid = parse_user_id(user_id)
    
    preview = DeletionService.get_deletion_preview(user_uuid, db)
    if not preview:
        raise HTTPException(status_code=404, detail="User not found")
    
    return preview


@router.delete("/{user_id}", status_code=200)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Soft delete a user and all their associated data"""
    user_uuid = parse_user_id(user_id)
    
    # Check if user exists
    if not UserService.get_user(user_uuid, db):
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Deleting user: {user_uuid}")
    result = DeletionService.soft_delete_user(user_uuid, db)
    
    return result


@router.post("/{user_id}/restore", status_code=200)
def restore_user(user_id: str, db: Session = Depends(get_db)):
    """Restore a soft-deleted user and their data (within 7-day recovery window)"""
    user_uuid = parse_user_id(user_id)
    
    logger.info(f"Restoring user: {user_uuid}")
    result = DeletionService.restore_user(user_uuid, db)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
