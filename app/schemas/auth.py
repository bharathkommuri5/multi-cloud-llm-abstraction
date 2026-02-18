from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Optional, Literal


class GoogleAuthRequest(BaseModel):
    """Deprecated: use OAuthRequest instead."""
    id_token: str


class OAuthRequest(BaseModel):
    """OAuth authentication request for any provider."""
    provider: Literal["google", "microsoft", "github"]
    id_token: str = Field(..., description="OAuth ID token or authorization code from provider")
    
    
class RegisterRequest(BaseModel):
    """User registration via OAuth provider."""
    provider: Literal["google", "microsoft", "github"]
    id_token: str = Field(..., description="OAuth ID token or authorization code from provider")
    

class LoginRequest(BaseModel):
    """User login via OAuth provider."""
    provider: Literal["google", "microsoft", "github"]
    id_token: str = Field(..., description="OAuth ID token or authorization code from provider")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_email: str
    is_new_user: bool  # True if user was just created, False if existing
    provider: str  # Which OAuth provider was used

    model_config = ConfigDict(from_attributes=True)
