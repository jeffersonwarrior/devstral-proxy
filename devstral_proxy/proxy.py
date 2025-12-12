"""
Devstral Proxy - Core Proxy Logic
Handles the translation between OpenAI and Mistral API formats.
"""
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from .config import settings
from .utils import (
    log_message,
    normalize_content,
    convert_openai_to_mistral_message,
    validate_tool_call_correspondence,
    sanitize_request_body,
    sanitize_response_body,
)
logger = logging.getLogger("devstral_proxy")
class DevstralProxy:
    """
    Main proxy class handling request/response translation
    """
    def __init__(self):
        self.vllm_base = settings.VLLM_BASE
        self.debug = settings.DEBUG
        self.version = "1.0.0"
        self.start_time = datetime.now()
        self.model_settings = settings.MODEL_SPECIFIC_SETTINGS
    def get_model_settings(self, model_name: str) -> dict:
        """
        Get model-specific settings
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary of model-specific settings or default settings
        """
        # Extract base model name (handle aliases)
        base_model = model_name.split("-")[0] if "-" in model_name else model_name
        
        # Try to find exact match first
        if model_name in self.model_settings:
            return self.model_settings[model_name]
        
        # Try base model name
        if base_model in self.model_settings:
            return self.model_settings[base_model]
        
        # Return default settings
        return {
            "tool_call_format": "mistral",
            "requires_strict_validation": False,
            "max_tool_calls": 5,
            "tool_call_timeout": 30.0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Return health status and configuration
        """
        uptime = str(datetime.now() - self.start_time)
        return {
            "status": "ok",
            "proxy": "Devstral Proxy",
            "version": self.version,
            "uptime": uptime,
            "vllm_target": self.vllm_base,
            "debug_mode": self.debug,
            "supported_models": list(self.model_settings.keys()),
            "timestamp": datetime.now().isoformat(),
        }
    async def handle_chat_completion(self, request: Request):
        """
        Handle chat completion requests
        Converts OpenAI format to Mistral format and forwards to VLLM server.
        """
        request_id = f"req-{int(time.time())}-{os.getpid()}"
        client_ip = request.client.host if request.client else "unknown"
        log_message(f"[{request_id}] Request from {client_ip}", level="info")
        try:
            start_time = time.time()
            # Parse request body
            try:
                body = await request.json()
                log_message(f"[{request_id}] Request: {json.dumps(body, indent=2, default=str)}", level="debug")
            except json.JSONDecodeError as e:
                log_message(f"[{request_id}] Invalid JSON: {str(e)}", level="error")
                return JSONResponse(
                    content={"error": f"Invalid JSON: {str(e)}"},
                    status_code=400,
                )
            # Sanitize and convert request
            try:
                sanitized_body = sanitize_request_body(body)
                # Log tool information if present
                original_tools = body.get("tools", [])
                if original_tools:
                    tool_names = [tool.get("function", {}).get("name", "unknown") for tool in original_tools]
                    log_message(f"[{request_id}] Found {len(original_tools)} tools: {', '.join(tool_names)}", level="info")
                # Check for tool calls in messages
            except Exception as e:
                log_message(f"[{request_id}] Sanitization error: {str(e)}", level="error")
                return JSONResponse(
                    content={"error": f"Request sanitization failed: {str(e)}"},
                    status_code=400,
                )
            # Forward to VLLM server
            try:
                async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
                    # Forward headers (excluding sensitive ones)
                    fwd_headers = {
                        k: v for k, v in request.headers.items()
                        if k.lower() not in {"host", "content-length", "accept-encoding"}
                    }
                    log_message(f"[{request_id}] Forwarding to {self.vllm_base}", level="debug")
                    resp = await client.post(
                        f"{self.vllm_base}/v1/chat/completions",
                        json=sanitized_body,
                        headers=fwd_headers,
                    )
            except httpx.HTTPError as e:
                log_message(f"[{request_id}] VLLM connection error: {str(e)}", level="error")
                return JSONResponse(
                    content={"error": f"VLLM server error: {str(e)}"},
                    status_code=502,
                )
            # Process response
            try:
                response_data = resp.json()
                sanitized_response = sanitize_response_body(response_data)
                # Log tool call information from response
                if "choices" in sanitized_response:
                    for i, choice in enumerate(sanitized_response["choices"]):
                        if "message" in choice and "tool_calls" in choice["message"]:
                            tool_calls = choice["message"]["tool_calls"]
                            if tool_calls:
                                tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                                log_message(f"[{request_id}] Response contains {len(tool_calls)} tool calls: {', '.join(tool_names)}", level="info")
                                # Check for tool call loops
                                    # Check if this is a legitimate VIBE request
                                # Log each tool call details
                                for j, tool_call in enumerate(tool_calls):
                                    func_name = tool_call.get("function", {}).get("name", "unknown")
                                    func_args = tool_call.get("function", {}).get("arguments", "{}")
                                    log_message(f"[{request_id}] Tool call {j+1}: {func_name}({func_args})", level="debug")
                duration = time.time() - start_time
                log_message(f"[{request_id}] Response: {resp.status_code} in {duration:.3f}s", level="info")
                log_message(f"[{request_id}] Response: {json.dumps(sanitized_response, indent=2, default=str)}", level="debug")
                return JSONResponse(
                    content=sanitized_response,
                    status_code=resp.status_code,
                    media_type="application/json",
                )
            except json.JSONDecodeError:
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    media_type=resp.headers.get("content-type", "application/json"),
                )
        # Check if we've exceeded the limit
        if len(self.) >= self.:
            # Trigger circuit breaker for 5 minutes
        # Add current timestamp
        self..append(now)
        return False
        # Create a signature for this tool call
        # Add to history
        # Keep history within limits
        # Check for repeated patterns in the detection window
        if signature_count > self.:
            log_message(f": {signature_count} identical tool calls in window", level="warning")
            return True
        return False
        # Create signature from function names and arguments
        signature_parts = []
        for call in sorted_calls:
            func_name = call.get("function", {}).get("name", "unknown")
            func_args = call.get("function", {}).get("arguments", "{}")
            signature_parts.append(f"{func_name}({func_args})")
        return ", ".join(signature_parts)
        # Check for VIBE-specific patterns
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                # VIBE CLI often mentions specific tools or has structured requests
                if any(keyword in content for keyword in ["search_replace", "read_file", "grep", "bash", "todo"]):
                    return True
        # Check if tools are reasonable (not system prompt)
        tools = body.get("tools", [])
        if tools:
            tool_names = [tool.get("function", {}).get("name", "") for tool in tools]
            # VIBE tools are specific
            if any(name in ["search_replace", "read_file", "write_file", "grep", "bash", "todo"] for name in tool_names):
                return True
        return False
        except Exception as e:
            log_message(f"[{request_id}] Unexpected error: {str(e)}", level="error")
            if self.debug:
                import traceback
                log_message(f"[{request_id}] Traceback: {traceback.format_exc()}", level="error")
            return JSONResponse(
                content={"error": f"Proxy error: {str(e)}"},
                status_code=500,
            )