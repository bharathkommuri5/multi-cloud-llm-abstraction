import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure base logger
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.
    
    Logs are written to:
    - logs/app.log (all levels)
    - Console (INFO and above)
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured (avoid duplicate handlers)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (all levels, with rotation)
        file_handler = RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=10485760,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Pre-configured loggers for common modules
auth_logger = get_logger("auth")
llm_logger = get_logger("llm")
provider_logger = get_logger("provider")
service_logger = get_logger("service")
database_logger = get_logger("database")
config_logger = get_logger("config")
