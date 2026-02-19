from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.auth import (
    OAuthRequest, RegisterRequest, LoginRequest, TokenResponse, GoogleAuthRequest
)
from app.core.config import settings
from app.models.user import User
from app.utils.logger import auth_logger as logger
from app.utils.helpers import create_access_token
from app.services.oauth_service import OAuthProviderFactory
from pydantic import BaseModel, ConfigDict
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """User registration via OAuth provider.
    
    Accepts authentication token from any supported OAuth provider (Google, Microsoft, GitHub).
    Creates new user account if email not already registered.
    Returns access token for API requests.
    
    Args:
        payload: RegisterRequest with provider name and ID token
        db: Database session
        
    Returns:
        TokenResponse with access token, user info, and is_new_user=True
        
    Raises:
        400: Invalid provider or missing provider config
        401: Invalid or expired OAuth token
        409: User already registered (use login instead)
    """
    logger.info(f"Registration attempt via {payload.provider}")
    
    # Step 1: Get provider and verify it's supported
    try:
        provider = OAuthProviderFactory.get_provider(payload.provider)
    except ValueError as e:
        logger.warning(f"Unsupported provider: {payload.provider}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {str(e)}"
        )
    
    # Step 2: Verify OAuth token with provider
    try:
        oauth_user_data = provider.verify_token(payload.id_token)
        logger.info(f"{payload.provider.capitalize()} token verified: {oauth_user_data.get('email')}")
    except Exception as e:
        logger.warning(f"{payload.provider.capitalize()} token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid {payload.provider} token: {str(e)}"
        )
    
    email = oauth_user_data.get("email")
    name = oauth_user_data.get("name") or email.split("@")[0]
    
    if not email:
        logger.warning(f"{payload.provider.capitalize()} token did not provide email")
        raise HTTPException(
            status_code=400,
            detail=f"{payload.provider.capitalize()} token did not provide email"
        )
    
    # Step 3: Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.warning(f"User registration failed: email already exists ({email})")
        raise HTTPException(
            status_code=409,
            detail=f"User with email {email} already registered. Use login instead."
        )
    
    # Step 4: Create new user account
    logger.info(f"Creating new user via {payload.provider}: {email}")
    user = User(username=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Step 5: Issue backend access token (JWT)
    if not settings.JWT_SECRET:
        logger.error("JWT secret not configured")
        raise HTTPException(status_code=500, detail="Server JWT secret not configured")
    
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    logger.info(f"Access token issued for new user {user.id} via {payload.provider}")
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        user_email=user.email,
        is_new_user=True,
        provider=payload.provider,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """User login via OAuth provider.
    
    Accepts authentication token from any supported OAuth provider (Google, Microsoft, GitHub).
    User must be pre-registered. Returns access token for API requests.
    
    Args:
        payload: LoginRequest with provider name and ID token
        db: Database session
        
    Returns:
        TokenResponse with access token, user info, and is_new_user=False
        
    Raises:
        400: Invalid provider or missing provider config
        401: Invalid or expired OAuth token
        404: User not found (use register first)
    """
    logger.info(f"Login attempt via {payload.provider}")
    
    # Step 1: Get provider and verify it's supported
    try:
        provider = OAuthProviderFactory.get_provider(payload.provider)
    except ValueError as e:
        logger.warning(f"Unsupported provider: {payload.provider}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {str(e)}"
        )
    
    # Step 2: Verify OAuth token with provider
    try:
        oauth_user_data = provider.verify_token(payload.id_token)
        logger.info(f"{payload.provider.capitalize()} token verified: {oauth_user_data.get('email')}")
    except Exception as e:
        logger.warning(f"{payload.provider.capitalize()} token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid {payload.provider} token: {str(e)}"
        )
    
    email = oauth_user_data.get("email")
    
    if not email:
        logger.warning(f"{payload.provider.capitalize()} token did not provide email")
        raise HTTPException(
            status_code=400,
            detail=f"{payload.provider.capitalize()} token did not provide email"
        )
    
    # Step 3: Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning(f"Login failed: user not found ({email})")
        raise HTTPException(
            status_code=404,
            detail=f"User with email {email} not found. Please register first."
        )
    
    logger.info(f"Existing user login via {payload.provider}: {email}")
    
    # Step 4: Issue backend access token (JWT)
    if not settings.JWT_SECRET:
        logger.error("JWT secret not configured")
        raise HTTPException(status_code=500, detail="Server JWT secret not configured")
    
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    logger.info(f"Access token issued for user {user.id} via {payload.provider}")
    
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        user_email=user.email,
        is_new_user=False,
        provider=payload.provider,
    )


@router.post("/google", response_model=TokenResponse, deprecated=True)
def google_sign_in(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Deprecated: Use /auth/register or /auth/login with provider='google' instead.
    
    Gmail login/register flow (auto-detects whether to register or login).
    Kept for backward compatibility.
    
    Verifies Google ID token, checks if user exists:
    - If new: creates user account automatically (register)
    - If existing: authenticates user (login)
    
    Returns access token for API requests.
    """
    logger.info("Gmail authentication attempt initiated (deprecated endpoint)")
    
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("Google client ID not configured")
        raise HTTPException(status_code=500, detail="Google client ID not configured on server")

    # Use Google provider from factory
    try:
        provider = OAuthProviderFactory.get_provider("google")
        oauth_user_data = provider.verify_token(payload.id_token)
        logger.info(f"Google ID token verified successfully")
    except Exception as e:
        logger.warning(f"Google ID token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {str(e)}")

    # Extract user info from token
    email = oauth_user_data.get("email")
    name = oauth_user_data.get("name") or email.split("@")[0]

    if not email:
        logger.warning("Google token did not provide email")
        raise HTTPException(status_code=400, detail="Google token did not provide email")

    # Check if user exists (login) or create (register)
    user = db.query(User).filter(User.email == email).first()
    is_new_user = False
    
    if not user:
        # Register: create new user account automatically
        logger.info(f"New user registration via Gmail: {email}")
        user = User(username=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    else:
        # Login: existing user
        logger.info(f"Existing user login via Gmail: {email}")

    # Issue backend access token (JWT)
    if not settings.JWT_SECRET:
        logger.error("JWT secret not configured")
        raise HTTPException(status_code=500, detail="Server JWT secret not configured")

    token = create_access_token(
        subject=str(user.id),
        email=user.email,
    )
    logger.info(f"Access token issued for user {user.id} (new_user={is_new_user})")

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        user_email=user.email,
        is_new_user=is_new_user,
        provider="google",
    )


class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    email: str

    model_config = ConfigDict(from_attributes=True)


@router.post("/logout", status_code=200)
def logout(request: Request):
    """Logout endpoint (token revocation stub).
    
    Notes:
    - JWT tokens are stateless, so logout is client-side by discarding token
    - This endpoint is informational but included for API completeness
    - For production: implement token blacklist if needed
    """
    user_id = getattr(request.state, "user_id", "unknown")
    logger.info(f"User {user_id} logged out")
    return {"message": "Successfully logged out. Discard the access token on client."}


@router.get("/providers")
def get_available_providers():
    """Get list of available OAuth providers.
    
    Returns configured and enabled providers available for login/register.
    Useful for frontend to render provider-specific sign-in buttons dynamically.
    
    Returns:
        List of provider names (e.g., ["google", "microsoft", "github"])
    """
    try:
        providers = OAuthProviderFactory.get_supported_providers()
        logger.info(f"Available providers requested: {providers}")
        return {"providers": providers}
    except Exception as e:
        logger.error(f"Error fetching available providers: {str(e)}")
        return {"providers": []}


@router.get("/profile", response_model=UserProfileResponse)
def get_current_user_profile(request: Request):
    """Get current authenticated user's profile.
    
    Requires valid Authorization header with Bearer token.
    Returns user ID and email from JWT token claims.
    """
    user_id = getattr(request.state, "user_id", None)
    user_email = getattr(request.state, "user_email", None)
    
    if not user_id or not user_email:
        logger.warning("Profile request with missing user info in token")
        raise HTTPException(status_code=401, detail="Invalid token claims")
    
    logger.info(f"Profile requested for user {user_id}")
    return UserProfileResponse(user_id=user_id, email=user_email)