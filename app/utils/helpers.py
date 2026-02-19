"""
Reusable utility functions for the application.
Covers validation, parsing, formatting, and common operations.
"""

from uuid import UUID
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import jwt
from app.core.config import settings
from app.utils.logger import service_logger as logger


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_uuid(user_id: str) -> UUID:
    """Validate and convert string to UUID."""
    try:
        return UUID(user_id)
    except ValueError as e:
        logger.warning(f"Invalid UUID format: {user_id}")
        raise ValueError(f"Invalid user ID format: {str(e)}")


def validate_temperature(temp: float) -> bool:
    """Check if temperature is within valid range (0-1)."""
    return 0.0 <= temp <= 1.0


def validate_max_tokens(tokens: int, max_limit: int = 4096) -> bool:
    """Check if max_tokens is within acceptable range."""
    return 0 < tokens <= max_limit


def validate_provider_name(provider: str) -> bool:
    """Check if provider is supported."""
    supported_providers = ["azure", "bedrock", "google", "grok"]
    return provider.lower() in supported_providers


# ============================================================================
# Token/JWT Utilities
# ============================================================================

def create_access_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Typically user ID
        email: User email for token claims
        expires_delta: Optional custom expiry duration
        additional_claims: Additional claims to include
        
    Returns:
        Encoded JWT token string
    """
    if not settings.JWT_SECRET:
        logger.error("JWT_SECRET not configured - cannot create token")
        raise RuntimeError("JWT secret not configured")
    
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": subject,
        "email": email,
        "iat": now,
        "exp": expire,
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    try:
        token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
        logger.debug(f"Access token created for {email}")
        return token
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    if not settings.JWT_SECRET:
        logger.error("JWT_SECRET not configured - cannot verify token")
        raise RuntimeError("JWT secret not configured")
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise


# ============================================================================
# String & Formatting Utilities
# ============================================================================

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max_length and add suffix if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_error_message(error: Exception, include_type: bool = True) -> str:
    """Format exception as user-friendly message."""
    msg = str(error)
    if include_type:
        return f"{error.__class__.__name__}: {msg}"
    return msg


def normalize_provider_name(provider: str) -> str:
    """Normalize provider name to lowercase."""
    return provider.lower().strip()


# ============================================================================
# Parsing Utilities
# ============================================================================

def safe_get_dict_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dict with fallback."""
    try:
        return data.get(key, default)
    except (TypeError, AttributeError):
        logger.warning(f"Failed to extract {key} from data")
        return default


def parse_comma_separated(text: str) -> list:
    """Parse comma-separated string into list."""
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


# ============================================================================
# Time Utilities
# ============================================================================

def get_expiry_time(minutes: int) -> datetime:
    """Get a future datetime by adding minutes to now."""
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_expired(expiry_time: datetime) -> bool:
    """Check if a given expiry time has passed."""
    return datetime.utcnow() > expiry_time


# ============================================================================
# Logging Context Utilities
# ============================================================================

def log_request_context(correlation_id: str, user_id: str, action: str, details: str = "") -> None:
    """Log request context in standardized format."""
    msg = f"[{correlation_id}] {action} | user: {user_id}"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_provider_operation(provider: str, model: str, operation: str, status: str) -> None:
    """Log provider operation in standardized format."""
    logger.info(f"Provider: {provider} | Model: {model} | Operation: {operation} | Status: {status}")
