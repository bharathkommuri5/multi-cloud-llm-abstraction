from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from app.core.config import settings
from app.core.logger import auth_logger as logger

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Simple bearer token check. Returns the token when valid."""
    token = credentials.credentials if credentials else None
    if not token or not settings.API_TOKEN:
        logger.warning("Authorization attempt without valid credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if token != settings.API_TOKEN:
        logger.warning("Authorization attempt with invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    logger.debug("Bearer token validated successfully")
    return token
