from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.core.config import settings
from app.models.user import User
from app.core import config
from app.core.logger import auth_logger as logger
import time
import jwt

# Google verification
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as grequests

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/google", response_model=TokenResponse)
def google_sign_in(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verify Google ID token, upsert user, and return backend access token."""
    logger.info("Google sign-in attempt initiated")
    
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("Google client ID not configured")
        raise HTTPException(status_code=500, detail="Google client ID not configured on server")

    try:
        google_payload = google_id_token.verify_oauth2_token(
            payload.id_token, grequests.Request(), settings.GOOGLE_CLIENT_ID
        )
        logger.info(f"Google ID token verified successfully")
    except Exception as e:
        logger.warning(f"Google ID token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {str(e)}")

    # google_payload contains email, sub (google user id), name, etc.
    email = google_payload.get("email")
    name = google_payload.get("name") or email.split("@")[0]

    if not email:
        logger.warning("Google token did not provide email")
        raise HTTPException(status_code=400, detail="Google token did not provide email")

    # Upsert user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.info(f"Creating new user from Google sign-in: {email}")
        user = User(username=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        logger.info(f"Existing user authenticated via Google sign-in: {email}")

    # Issue backend JWT access token
    now = int(time.time())
    exp = now + int(settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60

    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": exp,
    }

    if not settings.JWT_SECRET:
        logger.error("JWT secret not configured")
        raise HTTPException(status_code=500, detail="Server JWT secret not configured")

    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    logger.info(f"Access token issued for user {user.id}")

    return TokenResponse(access_token=token)
