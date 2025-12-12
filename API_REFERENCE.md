# Devstral Proxy API Reference

## Overview

The Devstral Proxy translates between OpenAI and Mistral API formats, allowing OpenAI-compatible clients to work seamlessly with Mistral AI models.

## Base URL

```
http://localhost:9000
```

## Endpoints

### 1. Chat Completions

Translate between OpenAI and Mistral chat completion APIs.

#### OpenAI Format → Mistral

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer your-api-key
```

**Request Body (OpenAI Format):**
```json
{
  "model": "devstral-small-2",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name"
            }
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

**Response (OpenAI Format):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "devstral-small-2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'm doing well, thank you!",
        "tool_calls": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 9,
    "total_tokens": 19
  }
}
```

#### Tool Call Example

**Request with Tools:**
```json
{
  "model": "devstral-small-2",
  "messages": [
    {
      "role": "user",
      "content": "What's the weather in San Francisco?"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

**Response with Tool Calls:**
```json
{
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\":\"San Francisco\"}"
            },
            "index": 0
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### 2. Health Check

Check the health status of the proxy service.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vllm_status": "connected",
  "uptime": "2h 15m 30s"
}
```

### 3. Root Endpoint

Get basic information about the proxy service.

```http
GET /
```

**Response:**
```json
{
  "name": "Devstral Proxy",
  "version": "1.0.0",
  "description": "Mistral ↔ OpenAI Translation Proxy",
  "endpoints": {
    "chat_completions": "/v1/chat/completions",
    "health": "/health"
  },
  "documentation": "https://github.com/your-repo/devstral-proxy"
}
```

## Translation Details

### OpenAI → Mistral Translation

The proxy converts OpenAI requests to Mistral format:

1. **Tool Calls**: Removes `index` field from tool calls
2. **Messages**: Normalizes content structure
3. **Parameters**: Maps parameter names correctly
4. **Streaming**: Maintains streaming functionality

### Mistral → OpenAI Translation

Responses are converted back to OpenAI format:

1. **Tool Calls**: Restores `index` field
2. **Errors**: Standardizes error format
3. **Usage**: Calculates token usage if needed
4. **Metadata**: Adds OpenAI-compatible metadata

## Streaming Support

The proxy supports streaming responses:

```http
POST /v1/chat/completions
Content-Type: application/json
```

**Request:**
```json
{
  "model": "devstral-small-2",
  "messages": [{"role": "user", "content": "Tell me a story"}],
  "stream": true
}
```

**Streaming Response:**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"devstral-small-2","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"devstral-small-2","choices":[{"index":0,"delta":{"content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"devstral-small-2","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"devstral-small-2","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "message": "Invalid request: model not found",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `invalid_request_error` | Request format or validation error |
| `authentication_error` | Invalid API key or auth |
| `permission_error` | Insufficient permissions |
| `not_found_error` | Resource not found |
| `rate_limit_error` | Rate limit exceeded |
| `api_error` | Internal server error |

## Model Support

The proxy supports multiple Devstral models:

### Model Configurations

| Model | Tool Support | Max Tokens | Notes |
|-------|--------------|------------|-------|
| `devstral-small-2` | Yes | 4096 | Mistral tool call format |
| `devstral-small` | Yes | 4096 | Similar to small-2 |
| `devstral-2` | Yes | 8192 | Enhanced capabilities |

### Model-Specific Behaviors

1. **Tool Call Format**: Each model has specific tool call requirements
2. **Validation Levels**: Strictness varies by model
3. **Parallel Tools**: Support varies by model
4. **Timeouts**: Different timeout configurations

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_BASE` | `http://127.0.0.1:8000` | VLLM server URL |
| `PROXY_HOST` | `0.0.0.0` | Proxy server host |
| `PROXY_PORT` | `9000` | Proxy server port |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `info` | Logging level |
| `LOG_FILE` | `/var/log/vllm-proxy.log` | Log file path |

## Rate Limiting

Current version supports basic rate limiting:

- **Default**: 100 requests per minute
- **Burst**: 10 requests per second
- **Per IP**: Applied to each client IP

## Authentication

Authentication is planned for future releases. Current version accepts all requests.

## SDK Integrations

### Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:9000")
response = client.post("/v1/chat/completions", json={
    "model": "devstral-small-2",
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

### JavaScript

```javascript
const response = await fetch('http://localhost:9000/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'devstral-small-2',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});
```

### curl

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "devstral-small-2",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

For more information, see the [main README](README.md) or [development guide](AGENTS.md).