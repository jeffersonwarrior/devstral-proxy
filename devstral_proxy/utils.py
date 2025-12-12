"""
Devstral Proxy - Utility Functions

Core utility functions for message conversion and validation.
"""

import logging
from typing import Dict, List, Any, Optional

from .config import settings

logger = logging.getLogger("devstral_proxy")


def log_message(message: str, level: str = "info"):
    """
    Log a message with the specified level
    
    Args:
        message: Message to log
        level: Log level (debug, info, warning, error)
    """
    if level == "debug" and not settings.DEBUG:
        return
    
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)


def normalize_content(content: Any) -> str:
    """
    Normalize OpenAI-style content to plain string
    
    Args:
        content: Content to normalize (can be str, list, or None)
        
    Returns:
        Normalized string content
    """
    if content is None:
        return ""
    
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_content = part.get("text") or ""
                if isinstance(text_content, str):
                    texts.append(text_content)
        return "\n".join(texts).strip()
    
    return str(content)


def convert_openai_to_mistral_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert single OpenAI message to Mistral format
    
    Args:
        msg: OpenAI format message
        
    Returns:
        Mistral format message or None if message should be dropped
    """
    role = msg.get("role")
    log_message(f"Converting message with role: {role}", level="debug")
    
    # Drop tool messages for Mistral
    if role == "tool":
        log_message(f"Dropping tool message: {msg.get('content', 'N/A')}", level="debug")
        return None
    
    # Handle assistant messages
    if role == "assistant":
        msg_copy = dict(msg)
        log_message(f"Processing assistant message", level="debug")
        
        # Convert OpenAI tool calls to Mistral format
        if "tool_calls" in msg_copy:
            openai_tool_calls = msg_copy["tool_calls"]
            mistral_tool_calls = []
            
            log_message(f"Found {len(openai_tool_calls)} tool calls to convert", level="debug")
            
            for tool_call in openai_tool_calls:
                log_message(f"Converting tool call: {tool_call.get('function', {}).get('name', 'unknown')}", level="debug")
                
                # Remove 'index' field
                if "index" in tool_call:
                    tool_call = dict(tool_call)
                    tool_call.pop("index", None)
                    log_message(f"Removed index field from tool call", level="debug")
                
                if isinstance(tool_call, dict) and "id" in tool_call and "function" in tool_call:
                    mistral_tool_calls.append({
                        "id": tool_call["id"],
                        "type": tool_call.get("type", "function"),
                        "function": tool_call["function"]
                    })
                    log_message(f"Converted tool call to Mistral format: {tool_call['function']['name']}", level="debug")
            
            msg_copy["tool_calls"] = mistral_tool_calls if mistral_tool_calls else None
            log_message(f"Final tool calls count: {len(mistral_tool_calls) if mistral_tool_calls else 0}", level="debug")
        
        # Normalize content
        content = normalize_content(msg_copy.get("content"))
        msg_copy["content"] = content if content else None
        log_message(f"Normalized content length: {len(content) if content else 0}", level="debug")
        
        # Mistral requires content OR tool_calls
        if msg_copy.get("content") is None and msg_copy.get("tool_calls") is None:
            log_message("Message has neither content nor tool_calls - dropping", level="debug")
            return None
        
        log_message("Successfully converted assistant message", level="debug")
        return msg_copy
    
    # Handle other roles
    if role in ["user", "system"]:
        msg_copy = dict(msg)
        content = normalize_content(msg_copy.get("content"))
        msg_copy["content"] = content if content else ""
        log_message(f"Processed {role} message with content length: {len(content)}", level="debug")
        return msg_copy
    
    log_message(f"Unknown message role '{role}' - dropping", level="warning")
    return None


def validate_tool_call_correspondence(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure tool calls have responses
    
    Mistral requires that tool calls must be followed by tool responses.
    This function removes messages with tool calls that don't have corresponding responses.
    
    Args:
        messages: List of messages to validate
        
    Returns:
        Filtered list of messages
    """
    filtered_messages = []
    pending_tool_call_ids = []
    
    for msg in messages:
        if msg.get("role") == "tool":
            continue
        
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tool_call in msg["tool_calls"]:
                pending_tool_call_ids.append(tool_call["id"])
        
        filtered_messages.append(msg)
    
    # Remove messages with tool calls that have no responses
    if pending_tool_call_ids:
        final_messages = []
        tool_call_index = 0
        
        for msg in filtered_messages:
            if (msg.get("role") == "assistant" and 
                msg.get("tool_calls") and 
                tool_call_index < len(pending_tool_call_ids)):
                tool_call_index += len(msg["tool_calls"])
            else:
                final_messages.append(msg)
        
        return final_messages
    
    return filtered_messages


def sanitize_request_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize request for Mistral
    
    Converts OpenAI format to Mistral format and validates the request.
    
    Args:
        body: OpenAI format request body
        
    Returns:
        Mistral format request body
    """
    body_copy = dict(body)
    
    # Convert messages
    original_messages = body_copy.get("messages", [])
    mistral_messages = []
    
    for msg in original_messages:
        converted = convert_openai_to_mistral_message(msg)
        if converted is not None:
            mistral_messages.append(converted)
    
    # Validate tool call correspondence
    mistral_messages = validate_tool_call_correspondence(mistral_messages)
    
    # Handle generation flags
    if body_copy.get("add_generation_prompt") and body_copy.get("continue_final_message"):
        body_copy.pop("continue_final_message", None)
    
    # Add dummy user message if needed
    if mistral_messages and mistral_messages[-1].get("role") == "assistant":
        if body_copy.get("add_generation_prompt", True):
            mistral_messages.append({"role": "user", "content": " "})
    
    body_copy["messages"] = mistral_messages
    return body_copy


def sanitize_response_body(response_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize response for OpenAI
    
    Converts Mistral format to OpenAI format.
    
    Args:
        response_body: Mistral format response body
        
    Returns:
        OpenAI format response body
    """
    if not isinstance(response_body, dict):
        return response_body
    
    response_copy = dict(response_body)
    
    # Add index fields back to tool calls
    if "choices" in response_copy:
        for choice in response_copy["choices"]:
            if "message" in choice and "tool_calls" in choice["message"]:
                tool_calls = choice["message"]["tool_calls"]
                if tool_calls:
                    for idx, tool_call in enumerate(tool_calls):
                        tool_call["index"] = idx
    
    return response_copy