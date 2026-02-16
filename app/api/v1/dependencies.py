"""
API v1 endpoint dependencies
"""
from uuid import UUID
from fastapi import HTTPException


def parse_user_id(user_id: str) -> UUID:
    """Parse and validate user ID from string to UUID"""
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
