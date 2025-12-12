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
    def _detect_task_request(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if this is a task execution request (not just a chat message)
        
        Returns task metadata if detected, None otherwise
        """
        messages = body.get("messages", [])
        if not messages:
            return None
        
        last_message = messages[-1]
        content = normalize_content(last_message.get("content", ""))
        
        # Detect task patterns
        task_indicators = [
            "do these items",
            "implement these",
            "create these",
            "write these",
            "fix these",
            "complete these items",
            "execute these tasks",
            "proceed with",
            "start implementing"
        ]
        
        content_lower = content.lower()
        detected_task = None
        
        for indicator in task_indicators:
            if indicator in content_lower:
                detected_task = indicator
                break
        
        if detected_task:
            return {
                "type": "task_execution",
                "trigger": detected_task,
                "content": content,
                "requires_tool_execution": True
            }
        
        return None

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
            
            # Detect task execution requests
            task_metadata = self._detect_task_request(body)
            if task_metadata:
                log_message(f"[{request_id}] TASK EXECUTION DETECTED: {task_metadata['trigger']}", level="info")
                log_message(f"[{request_id}] Task requires actual tool execution (not just LLM response)", level="warning")
                # Force tool calling by setting tool_choice
                body["tool_choice"] = "required"
                log_message(f"[{request_id}] Set tool_choice=required to force tool execution", level="info")
                
                # Add instruction to ensure the model actually executes tools
                if body.get("messages"):
                    # Find or create system message
                    system_msg = None
                    for msg in body["messages"]:
                        if msg.get("role") == "system":
                            system_msg = msg
                            break
                    
                    execution_instruction = """CRITICAL INSTRUCTION - TASK EXECUTION MODE:
You are in TASK EXECUTION mode. Your response MUST include tool calls to complete the requested items.
- Do NOT respond with generic messages like "Task completed" without actually calling tools
- You MUST use the available tools to perform the actual work
- Every request item must have a corresponding tool call
- Failure to call tools is a critical error"""
                    
                    if system_msg:
                        system_msg["content"] += "\n\n" + execution_instruction
                    else:
                        body["messages"].insert(0, {
                            "role": "system",
                            "content": execution_instruction
                        })
            # Sanitize and convert request
            try:
                original_streaming = body.get("stream", False)
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
                
                # Validate task execution response
                if task_metadata:
                    has_tool_calls = False
                    if "choices" in sanitized_response:
                        for choice in sanitized_response["choices"]:
                            if "message" in choice and choice["message"].get("tool_calls"):
                                has_tool_calls = True
                                break
                    
                    if not has_tool_calls:
                        log_message(f"[{request_id}] WARNING: Task execution request received no tool calls!", level="warning")
                        log_message(f"[{request_id}] Response was: {json.dumps(sanitized_response, indent=2, default=str)}", level="warning")
                
                # Log tool call information from response
                if "choices" in sanitized_response:
                    for i, choice in enumerate(sanitized_response["choices"]):
                        if "message" in choice and "tool_calls" in choice["message"]:
                            tool_calls = choice["message"]["tool_calls"]
                            if tool_calls:
                                tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                                log_message(f"[{request_id}] Response contains {len(tool_calls)} tool calls: {', '.join(tool_names)}", level="info")
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
            except Exception as e:
                log_message(f"[{request_id}] Unexpected error: {str(e)}", level="error")
                if self.debug:
                    import traceback
                    log_message(f"[{request_id}] Traceback: {traceback.format_exc()}", level="error")
                return JSONResponse(
                    content={"error": f"Proxy error: {str(e)}"},
                    status_code=500,
                )
        except Exception as e:
            log_message(f"[{request_id}] Unexpected outer error: {str(e)}", level="error")
            if self.debug:
                import traceback
                log_message(f"[{request_id}] Outer traceback: {traceback.format_exc()}", level="error")
            return JSONResponse(
                content={"error": f"Proxy outer error: {str(e)}"},
                status_code=500,
            )

    def _validate_tool_calls(self, tool_calls: List[Dict[str, Any]], model_name: str = "unknown") -> bool:
        """
        Validate tool calls against model-specific constraints
        
        Args:
            tool_calls: List of tool calls to validate
            model_name: Name of the model for specific validation rules
            
        Returns:
            True if tool calls are valid, False otherwise
        """
        if not tool_calls:
            return True
            
        model_settings = self.get_model_settings(model_name)
        max_tool_calls = model_settings.get("max_tool_calls", 10)
        
        # Check tool call count limit
        if len(tool_calls) > max_tool_calls:
            log_message(f"Tool call limit exceeded: {len(tool_calls)} > {max_tool_calls}", level="warning")
            return False
        
        # Validate each tool call structure
        for i, tool_call in enumerate(tool_calls):
            if "function" not in tool_call:
                log_message(f"Tool call {i+1} missing 'function' field", level="error")
                return False
                
            function = tool_call["function"]
            if "name" not in function or not function["name"]:
                log_message(f"Tool call {i+1} missing or empty 'name' field", level="error")
                return False
                
            if "arguments" not in function:
                log_message(f"Tool call {i+1} missing 'arguments' field", level="error")
                return False
        
        return True
    
    def _handle_tool_call_error(self, request_id: str, error: str, details: Dict[str, Any] = None) -> JSONResponse:
        """
        Handle tool call errors with detailed error information
        
        Args:
            request_id: Request ID for tracking
            error: Error message
            details: Additional error details
            
        Returns:
            JSONResponse with error information
        """
        error_response = {
            "error": error,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            error_response["details"] = details
            
        if self.debug:
            error_response["debug_info"] = {
                "proxy_version": self.version,
                "vllm_target": self.vllm_base,
                "model_settings": list(self.model_settings.keys())
            }
        
        log_message(f"[{request_id}] Tool call error: {error}", level="error")
        if details:
            log_message(f"[{request_id}] Error details: {json.dumps(details, indent=2, default=str)}", level="debug")
            
        return JSONResponse(
            content=error_response,
            status_code=400,
        )