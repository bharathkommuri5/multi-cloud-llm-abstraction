from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for user operations"""

    @staticmethod
    def create_user(user_data: UserCreate, db: Session) -> User:
        """Create a new user"""
        logger.info(f"Creating user: {user_data.username}")
        
        # Check if user already exists
        existing = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing:
            raise ValueError("User already exists")
        
        user = User(username=user_data.username, email=user_data.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user(user_id: UUID, db: Session) -> User:
        """Get a user by ID (active users only)"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        return user

    @staticmethod
    def get_all_users(db: Session, include_deleted: bool = False) -> list[User]:
        """Get all users"""
        if include_deleted:
            return db.query(User).all()
        return db.query(User).filter(User.deleted_at == None).all()

    @staticmethod
    def update_user(user_id: UUID, user_data: UserUpdate, db: Session) -> User:
        """Update user details (active users only)"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at == None
        ).first()
        
        if not user:
            raise ValueError("User not found or has been deleted")
        
        if user_data.username:
            user.username = user_data.username
        if user_data.email:
            user.email = user_data.email
        
        db.commit()
        db.refresh(user)
        return user
