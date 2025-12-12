"""
Devstral Proxy - Core module

A high-performance Mistral ↔ OpenAI translation proxy for seamless integration
between OpenAI-compatible clients and Mistral AI models.
"""

from .config import Settings
from .models import (
    OpenAIMessage,
    MistralMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from .proxy import DevstralProxy
from .utils import (
    normalize_content,
    convert_openai_to_mistral_message,
    validate_tool_call_correspondence,
    sanitize_request_body,
    sanitize_response_body,
)

__version__ = "1.0.0"
__author__ = "Devstral AI"
__license__ = "MIT"
__all__ = [
    "DevstralProxy",
    "Settings",
    "OpenAIMessage",
    "MistralMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "normalize_content",
    "convert_openai_to_mistral_message",
    "validate_tool_call_correspondence",
    "sanitize_request_body",
    "sanitize_response_body",
]