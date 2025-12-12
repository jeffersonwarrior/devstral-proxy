"""
Configuration management for Devstral Proxy
"""

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
        "/var/log/vllm-proxy.log",
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()