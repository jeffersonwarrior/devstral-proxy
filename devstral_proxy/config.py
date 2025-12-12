"""
Configuration management for Devstral Proxy
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Proxy configuration settings"""
    
    # VLLM Server Configuration
    VLLM_BASE: str = Field(
        "http://127.0.0.1:8000",
        description="Base URL for the VLLM server"
    )
    
    # Proxy Server Configuration
    PROXY_HOST: str = Field(
        "0.0.0.0",
        description="Host address for the proxy server"
    )
    PROXY_PORT: int = Field(
        9000,
        description="Port for the proxy server"
    )
    
    # Debug Configuration
    DEBUG: bool = Field(
        True,  # Changed to True for better tool call troubleshooting
        description="Enable debug mode for detailed logging"
    )
    
    # Logging Configuration
    LOG_FILE: str = Field(
        "/tmp/vllm-proxy.log",
        description="Path to the log file"
    )
    LOG_LEVEL: str = Field(
        "debug",  # Changed to debug for better tool call troubleshooting
        description="Logging level (debug, info, warning, error)"
    )
    
    # Performance Configuration
    TIMEOUT: Optional[int] = Field(
        None,
        description="Request timeout in seconds"
    )
    MAX_CONNECTIONS: int = Field(
        100,
        description="Maximum concurrent connections"
    )
    
    # Model-specific configurations
    MODEL_SPECIFIC_SETTINGS: dict = Field(
        default_factory=lambda: {
            "devstral-small-2": {
                "tool_call_format": "mistral",
                "requires_strict_validation": True,
                "max_tool_calls": 10,
                "tool_call_timeout": 30.0,
                "supports_parallel_tools": True,
                "max_parallel_tools": 3
            },
            "devstral-small": {
                "tool_call_format": "mistral",
                "requires_strict_validation": True,
                "max_tool_calls": 10,
                "tool_call_timeout": 30.0,
                "supports_parallel_tools": True,
                "max_parallel_tools": 3
            },
            "devstral-2": {
                "tool_call_format": "mistral",
                "requires_strict_validation": True,
                "max_tool_calls": 15,
                "tool_call_timeout": 45.0,
                "supports_parallel_tools": True,
                "max_parallel_tools": 5
            }
        },
        description="Model-specific configuration overrides"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Configure logging
def configure_logging():
    """Configure logging based on settings"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger("devstral_proxy")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    log_dir = os.path.dirname(settings.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for debug mode
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Configure logging when module is imported
logger = configure_logging()