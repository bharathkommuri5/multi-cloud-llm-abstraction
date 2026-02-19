"""
Authentication middleware for validating access tokens.
Checks JWT validity and extracts user information.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.logger import auth_logger as logger
from app.utils.helpers import verify_access_token
from app.core.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens and attach user info to request state.
    Skips validation for public routes.
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = {
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/auth/google",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Check token validity for protected routes."""
        
        # Skip auth check for public routes
        if request.url.path in self.PUBLIC_ROUTES:
            return await call_next(request)
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"Missing Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"}
            )
        
        # Extract token from "Bearer <token>"
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid auth scheme: {scheme}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            logger.warning(f"Malformed Authorization header")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Malformed Authorization header"}
            )
        
        # Verify token
        try:
            payload = verify_access_token(token)
            # Attach user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            logger.debug(f"Token validated for user {request.state.user_id}")
        except Exception as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Continue to next handler
        return await call_next(request)
