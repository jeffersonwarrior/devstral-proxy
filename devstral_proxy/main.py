"""
Devstral Proxy - Main Application

Entry point for the Devstral Proxy server.
"""

import os
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .proxy import DevstralProxy
from .utils import log_message

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("devstral_proxy")

# Create FastAPI app
app = FastAPI(
    title="Devstral Proxy",
    description="Mistral ↔ OpenAI Translation Proxy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize proxy
proxy = DevstralProxy()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Main chat completions endpoint
    
    Converts OpenAI format requests to Mistral format and forwards to VLLM server.
    """
    return await proxy.handle_chat_completion(request)


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint
    
    Returns proxy status and configuration information.
    """
    return proxy.health_check()


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint
    
    Returns basic proxy information.
    """
    return {
        "name": "Devstral Proxy",
        "version": "1.0.0",
        "description": "Mistral ↔ OpenAI Translation Proxy",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


def main() -> None:
    """
    Main entry point
    
    Starts the Devstral Proxy server.
    """
    # Ensure log directory exists
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    log_message("Starting Devstral Proxy...", level="info")
    log_message(f"Configuration: {settings.model_dump_json()}", level="debug")
    
    # Start server
    uvicorn.run(
        "devstral_proxy.main:app",
        host=settings.PROXY_HOST,
        port=settings.PROXY_PORT,
        reload=False,
        workers=1,
        log_level=settings.LOG_LEVEL,
    )


if __name__ == "__main__":
    main()