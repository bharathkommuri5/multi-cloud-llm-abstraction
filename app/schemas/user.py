from pydantic import BaseModel, EmailStr,ConfigDict
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserDeletionPreview(BaseModel):
    """Shows what will be deleted when user is soft-deleted"""
    user_id: UUID
    username: str
    email: str
    total_call_history_records: int
    total_hyperparameter_configs: int
    recovery_deadline: datetime  # 7 days from deletion
    message: str


class UserRestoreRequest(BaseModel):
    """Request to restore a soft-deleted user"""
    user_id: UUID
