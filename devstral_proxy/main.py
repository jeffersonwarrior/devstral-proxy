"""
Devstral Proxy - Main Application

Entry point for the Devstral Proxy server.
"""

import argparse
import os
from typing import Any, Dict, Optional, Sequence

from fastapi import FastAPI, Request
import uvicorn

from .config import configure_logging, settings
from .proxy import DevstralProxy
from .utils import log_message

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


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="devstral_proxy")
    parser.add_argument(
        "--enable-logging",
        action="store_true",
        help="Enable proxy application logging.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (allows debug-level logs when logging is enabled).",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default=None,
        help="Override log level.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Override log file path.",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable verbose development logging (equivalent to --enable-logging --debug --log-level debug).",
    )
    return parser.parse_args(argv)


def _apply_runtime_settings(args: argparse.Namespace) -> None:
    if args.dev:
        settings.LOGGING_ENABLED = True
        settings.DEBUG = True
        settings.LOG_LEVEL = "debug"

    if args.enable_logging:
        settings.LOGGING_ENABLED = True

    if args.debug:
        settings.DEBUG = True

    if args.log_level:
        settings.LOG_LEVEL = args.log_level

    if args.log_file:
        settings.LOG_FILE = args.log_file


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
    args = _parse_args()
    _apply_runtime_settings(args)
    configure_logging()

    if settings.LOGGING_ENABLED:
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
        access_log=settings.LOGGING_ENABLED,
    )


if __name__ == "__main__":
    main()