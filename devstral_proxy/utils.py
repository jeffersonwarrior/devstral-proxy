"""
Devstral Proxy - Utility Functions

Core utility functions for message conversion and validation.
"""

import json
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


def validate_task_execution_response(response: Dict[str, Any], request_id: str) -> bool:
    """
    Validate that a task execution response actually contains tool calls
    
    Args:
        response: Response from the LLM
        request_id: Request ID for logging
        
    Returns:
        True if response contains tool calls, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    choices = response.get("choices", [])
    for choice in choices:
        message = choice.get("message", {})
        if message.get("tool_calls"):
            return True
    
    log_message(f"[{request_id}] Task execution response missing tool calls", level="warning")
    return False


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
    
    # Handle tool messages for Mistral
    if role == "tool":
        msg_copy = dict(msg)
        content = msg_copy.get("content", "")
        tool_call_id = msg_copy.get("tool_call_id")
        
        log_message(f"Processing tool message with tool_call_id: {tool_call_id}, content length: {len(content) if content else 0}", level="debug")
        
        # Mistral requires both content and tool_call_id for tool messages
        if not tool_call_id:
            log_message("Tool message missing tool_call_id - cannot convert", level="warning")
            return None
        
        # Normalize content for Mistral
        if isinstance(content, list):
            # Handle list of content chunks
            content_str = ""
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("type") == "text":
                    content_str += chunk.get("text", "")
            msg_copy["content"] = content_str
        elif isinstance(content, str):
            msg_copy["content"] = content
        else:
            msg_copy["content"] = str(content) if content else ""
        
        log_message(f"Successfully converted tool message", level="debug")
        return msg_copy
    
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
                    # Enhanced Mistral format for Devstral models
                    mistral_tool_calls.append({
                        "id": tool_call["id"],
                        "type": tool_call.get("type", "function"),
                        "function": {
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"]
                        }
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
    Validate that tool messages correspond to tool calls
    
    Mistral requires that tool calls must be followed by tool responses.
    This function validates correspondence and warns about mismatches.
    
    Args:
        messages: List of messages to validate
        
    Returns:
        Filtered list of messages (tool messages are KEPT, not removed)
    """
    # Track tool calls and their corresponding results
    tool_call_ids = {}  # Maps tool_call_id to whether it has a result
    
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tool_call in msg["tool_calls"]:
                tool_call_id = tool_call.get("id")
                if tool_call_id:
                    tool_call_ids[tool_call_id] = False
        
        elif msg.get("role") == "tool" and msg.get("tool_call_id"):
            tool_call_ids[msg.get("tool_call_id")] = True
    
    # Warn about unmatched tool calls
    for tool_call_id, has_result in tool_call_ids.items():
        if not has_result:
            log_message(f"Warning: Tool call {tool_call_id} has no corresponding result message", level="warning")
    
    # Keep all messages including tool results
    return messages


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
    
    # Debug: Log original request body
    log_message(f"Original request body: {json.dumps(body_copy, indent=2, default=str)}", level="debug")
    
    # Convert messages
    original_messages = body_copy.get("messages", [])
    mistral_messages = []
    
    for msg in original_messages:
        converted = convert_openai_to_mistral_message(msg)
        if converted is not None:
            mistral_messages.append(converted)
    
    # Validate tool call correspondence
    mistral_messages = validate_tool_call_correspondence(mistral_messages)

    # Mistral validation is strict: tool_calls must be matched with tool responses 1:1
    # Remove tool responses that are problematic, then clean up orphaned tool_calls
    
    # First pass: identify all tool calls and responses
    tool_calls_by_id = {}
    for msg in mistral_messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_calls_by_id[tc.get("id")] = True
    
    tool_responses_by_id = {}
    for msg in mistral_messages:
        if msg.get("role") == "tool":
            tool_responses_by_id[msg.get("tool_call_id")] = True
    
    # Second pass: mark tool responses for removal if problematic
    messages_to_remove = []
    tool_ids_to_remove = set()
    
    for i, msg in enumerate(mistral_messages):
        if msg.get("role") == "tool":
            tool_call_id = msg.get("tool_call_id")
            is_last_message = (i == len(mistral_messages) - 1)
            is_orphaned = tool_call_id not in tool_calls_by_id
            
            # Check if followed by user without assistant in between
            next_is_user_without_assistant = False
            if i + 1 < len(mistral_messages):
                next_msg = mistral_messages[i + 1]
                if next_msg.get("role") == "user":
                    next_is_user_without_assistant = True
            
            # Remove if problematic
            if is_orphaned or is_last_message or next_is_user_without_assistant:
                log_message(f"Removing tool response (last={is_last_message}, orphaned={is_orphaned}, user_after={next_is_user_without_assistant}): {tool_call_id}", level="debug")
                messages_to_remove.append(i)
                tool_ids_to_remove.add(tool_call_id)
    
    # Remove tool messages
    for i in sorted(messages_to_remove, reverse=True):
        mistral_messages.pop(i)
    
    # Third pass: also remove tool_calls that don't have responses
    for i, msg in enumerate(mistral_messages):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            original_tcs = msg["tool_calls"]
            # Keep only tool_calls that have responses
            msg["tool_calls"] = [
                tc for tc in original_tcs
                if tc.get("id") in tool_responses_by_id and tc.get("id") not in tool_ids_to_remove
            ]
            
            removed_count = len(original_tcs) - len(msg["tool_calls"])
            if removed_count > 0:
                log_message(f"Removed {removed_count} orphaned tool_calls from assistant", level="debug")
            
            # If no tool_calls left, remove the field (don't set to None)
            if not msg["tool_calls"]:
                msg.pop("tool_calls", None)
                # Mistral requires content OR tool_calls - set placeholder if needed
                if msg.get("content") is None or msg.get("content") == "":
                    msg["content"] = " "
    
    # Handle generation flags
    if body_copy.get("add_generation_prompt") and body_copy.get("continue_final_message"):
        body_copy.pop("continue_final_message", None)
    
    # Add dummy user message if needed
    # Only add if last message is assistant (not tool)
    # Mistral doesn't allow user message directly after tool message
    if mistral_messages:
        last_role = mistral_messages[-1].get("role") if mistral_messages else None
        log_message(f"Last message role before dummy user: {last_role}, total messages: {len(mistral_messages)}", level="debug")
        if last_role == "assistant":
            if body_copy.get("add_generation_prompt", True):
                mistral_messages.append({"role": "user", "content": " "})
                log_message(f"Added dummy user message. Total messages now: {len(mistral_messages)}", level="debug")
    
    # Remove stream options if stream is False
    stream_value = body_copy.get("stream", False)
    log_message(f"Stream value: {stream_value}", level="debug")
    
    if not stream_value:
        # Check for and remove stream options - be very thorough
        stream_options_found = []
        
        # Remove top-level stream options (but preserve the "stream" key itself)
        for key in list(body_copy.keys()):
            # Remove keys containing "stream" but NOT the "stream" key itself
            if "stream" in key.lower() and key.lower() != "stream":
                stream_options_found.append(key)
                body_copy.pop(key, None)
        
        # Remove nested stream options in messages
        if "messages" in body_copy:
            for i, message in enumerate(body_copy["messages"]):
                if isinstance(message, dict):
                    for msg_key in list(message.keys()):
                        if "stream" in msg_key.lower():
                            stream_options_found.append(f"messages[{i}].{msg_key}")
                            message.pop(msg_key, None)
        
        # Remove stream options in tools
        if "tools" in body_copy:
            for i, tool in enumerate(body_copy["tools"]):
                if isinstance(tool, dict):
                    for tool_key in list(tool.keys()):
                        if "stream" in tool_key.lower():
                            stream_options_found.append(f"tools[{i}].{tool_key}")
                            tool.pop(tool_key, None)
                    # Check nested structures in tools
                    if "function" in tool and isinstance(tool["function"], dict):
                        for func_key in list(tool["function"].keys()):
                            if "stream" in func_key.lower():
                                stream_options_found.append(f"tools[{i}].function.{func_key}")
                                tool["function"].pop(func_key, None)
        
        # Remove stream options in other nested structures
        for key, value in list(body_copy.items()):
            if isinstance(value, dict):
                for sub_key in list(value.keys()):
                    if "stream" in sub_key.lower():
                        stream_options_found.append(f"{key}.{sub_key}")
                        value.pop(sub_key, None)
            elif isinstance(value, list):
                for j, item in enumerate(value):
                    if isinstance(item, dict):
                        for item_key in list(item.keys()):
                            if "stream" in item_key.lower():
                                stream_options_found.append(f"{key}[{j}].{item_key}")
                                item.pop(item_key, None)
        
        if stream_options_found:
            log_message(f"Removed stream-related options: {stream_options_found}", level="info")
        else:
            log_message("No stream-related options found to remove", level="debug")
    
    log_message(f"Final message sequence: {[(m.get('role'), m.get('content', '')[:50] if isinstance(m.get('content'), str) else '...') for m in mistral_messages]}", level="debug")
    body_copy["messages"] = mistral_messages
    
    # Debug: Log final sanitized body
    log_message(f"Sanitized request body: {json.dumps(body_copy, indent=2, default=str)}", level="debug")
    
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