"""
Utils package - provides logging and helper utilities.
"""

from app.utils.logger import (
    get_logger,
    auth_logger,
    llm_logger,
    provider_logger,
    service_logger,
    database_logger,
    config_logger,
)

from app.utils.helpers import (
    validate_uuid,
    validate_temperature,
    validate_max_tokens,
    validate_provider_name,
    create_access_token,
    verify_access_token,
    truncate_string,
    format_error_message,
    normalize_provider_name,
    safe_get_dict_value,
    parse_comma_separated,
    get_expiry_time,
    is_expired,
    log_request_context,
    log_provider_operation,
)

__all__ = [
    # Loggers
    "get_logger",
    "auth_logger",
    "llm_logger",
    "provider_logger",
    "service_logger",
    "database_logger",
    "config_logger",
    # Validation
    "validate_uuid",
    "validate_temperature",
    "validate_max_tokens",
    "validate_provider_name",
    # Token/JWT
    "create_access_token",
    "verify_access_token",
    # Formatting/Parsing
    "truncate_string",
    "format_error_message",
    "normalize_provider_name",
    "safe_get_dict_value",
    "parse_comma_separated",
    # Time
    "get_expiry_time",
    "is_expired",
    # Logging context
    "log_request_context",
    "log_provider_operation",
]
