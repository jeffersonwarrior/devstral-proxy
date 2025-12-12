"""
Devstral Proxy - Data Models

Pydantic models for request/response validation.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class OpenAIMessage(BaseModel):
    """OpenAI format message"""
    role: str = Field(..., description="Message role (system, user, assistant, tool)")
    content: Union[str, List[Dict[str, Any]], None] = Field(
        ..., 
        description="Message content (string or multi-part)"
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Tool calls (for assistant messages)"
    )


class MistralMessage(BaseModel):
    """Mistral format message"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: Optional[str] = Field(
        None, 
        description="Message content (string only)"
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Tool calls (for assistant messages)"
    )


class ChatCompletionRequest(BaseModel):
    """Chat completion request"""
    model: str = Field(..., description="Model name")
    messages: List[OpenAIMessage] = Field(..., description="Conversation messages")
    stream: bool = Field(False, description="Stream responses")
    temperature: Optional[float] = Field(
        None, 
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        None, 
        description="Maximum tokens to generate"
    )
    tool_choice: Optional[str] = Field(
        None, 
        description="Tool choice (auto, none, or specific tool)"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Available tools"
    )


class ChatCompletionChoice(BaseModel):
    """Single completion choice"""
    index: int = Field(..., description="Choice index")
    message: OpenAIMessage = Field(..., description="Generated message")
    finish_reason: str = Field(..., description="Reason for finishing")


class ChatCompletionResponse(BaseModel):
    """Chat completion response"""
    id: str = Field(..., description="Completion ID")
    object: str = Field(..., description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[ChatCompletionChoice] = Field(..., description="Completion choices")
    usage: Optional[Dict[str, Any]] = Field(
        None, 
        description="Token usage information"
    )


class ErrorResponse(BaseModel):
    """Error response"""
    error: Dict[str, Any] = Field(..., description="Error details")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Proxy status")
    proxy: str = Field(..., description="Proxy name")
    version: str = Field(..., description="Proxy version")
    uptime: str = Field(..., description="Proxy uptime")
    vllm_target: str = Field(..., description="VLLM server target")
    debug_mode: bool = Field(..., description="Debug mode status")
    timestamp: str = Field(..., description="Current timestamp")