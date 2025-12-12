# AGENTS.md - Devstral Proxy Developer Guide

This guide helps agents work effectively in the Devstral Proxy codebase.

## Project Overview

Devstral Proxy is a high-performance translation layer that converts between OpenAI and Mistral API formats. It enables OpenAI-compatible clients to seamlessly work with Mistral AI models through a VLLM server.

## Architecture

- **Proxy Server**: FastAPI + Uvicorn (default port: 9000)
- **Translation Layer**: Converts OpenAI ↔ Mistral formats
- **VLLM Integration**: Forwards requests to VLLM server (default: http://127.0.0.1:8000)
- **Async Processing**: Built on async/await patterns for high concurrency

## Essential Commands

### Running the Proxy
```bash
# Start the proxy server
python devstral_proxy/main.py

# Alternative with Poetry
poetry run python devstral_proxy/main.py
```

### Testing
```bash
# Quick test script - tests all functionality
python test_proxy.py

# QA test suite - comprehensive testing
python qa/run_tests.py

# Run specific tests with pytest
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black devstral_proxy/

# Sort imports
isort devstral_proxy/

# Type checking
mypy devstral_proxy/

# Run all quality checks (if available)
make lint  # or equivalent script
```

### Package Management
```bash
# Install dependencies
pip install -e .

# With Poetry
poetry install

# Update dependencies
poetry update
```

## Project Structure

```
devstral-proxy/
├── devstral_proxy/           # Main package
│   ├── main.py              # FastAPI application entry point
│   ├── proxy.py             # Core translation logic
│   ├── models.py            # Pydantic data models
│   ├── utils.py             # Utility functions
│   └── config.py            # Configuration management
├── qa/                      # QA testing suite
│   ├── run_tests.py         # QA test runner
│   └── test_data/           # Test data and fixtures
├── docs/                    # Documentation
│   └── architecture.md      # System architecture
├── test_proxy.py            # Quick functional tests
└── pyproject.toml          # Python project configuration
```

## Configuration

Configuration is managed through environment variables and `.env` file:

```env
# VLLM Server Configuration
VLLM_BASE=http://127.0.0.1:8000

# Proxy Server Configuration
PROXY_HOST=0.0.0.0
PROXY_PORT=9000

# Debug and Logging
DEBUG=true
LOG_LEVEL=debug
LOG_FILE=/var/log/vllm-proxy.log
```

Key configuration details:
- Settings are defined in `config.py` using Pydantic BaseSettings
- Model-specific configurations are stored in `MODEL_SPECIFIC_SETTINGS`
- Debug mode is enabled by default for troubleshooting tool calls
- Logging supports rotation with configurable levels

## Code Conventions

### Style Guidelines
- **Linting**: Black (88 char line length) + isort + mypy
- **Type Hints**: Required (mypy enforces no untyped definitions)
- **Docstrings**: Standard Python docstrings for all public functions
- **Logging**: Use structured logging via `utils.log_message()`

### Import Patterns
```python
# Standard library imports first
import os
import logging
from typing import Dict, Any

# Third-party imports
from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx

# Local imports
from .config import settings
from .utils import log_message
```

### Async Patterns
- All HTTP operations use async/await
- Use `httpx.AsyncClient` for HTTP requests
- FastAPI endpoint handlers are async
- Error handling includes proper async context management

## Key Components

### Proxy Translation (`proxy.py`)
- Core logic for OpenAI ↔ Mistral format conversion
- Handles tool calls, streaming, and message normalization
- Contains `DevstralProxy` class with main translation methods

### Data Models (`models.py`)
- Pydantic models for OpenAI and Mistral API formats
- Request/response validation and serialization
- Type-safe data structures

### Configuration (`config.py`)
- Environment-based configuration management
- Model-specific settings and overrides
- Logging configuration with rotation

### Utilities (`utils.py`)
- Helper functions for logging, validation
- Common data transformation utilities
- Error handling helpers

## API Endpoints

### Main Endpoints
- `POST /v1/chat/completions` - Chat completions with translation
- `GET /health` - Health check and status
- `GET /` - Root info and documentation links

### Translation Behavior
- Converts OpenAI tool calls to/from Mistral format
- Handles streaming responses correctly
- Maintains API compatibility while translating

## Testing Approach

### Test Types
- **Functional Tests**: `test_proxy.py` - quick integration tests
- **QA Suite**: `qa/run_tests.py` - comprehensive testing
- **Unit Tests**: `tests/` directory for component testing

### Test Patterns
- Use `httpx.AsyncClient` for async HTTP testing
- Test both success and error scenarios
- Include tool call functionality testing
- Verify translation accuracy

## Model-Specific Considerations

The proxy supports multiple Devstral models with unique configurations:
- `devstral-small-2`: Mistral tool call format, strict validation
- `devstral-small`: Similar to small-2 with parallel tool support
- `devstral-2`: Enhanced tool call capabilities and higher limits

Each model has specific:
- Tool call format requirements
- Validation strictness levels
- Maximum tool call limits
- Timeout configurations

## Common Gotchas

### Configuration Issues
- Always check `.env` file exists and is correctly formatted
- VLLM server must be running before proxy starts
- Log directory permissions matter for file logging

### Tool Call Translation
- Mistral format removes `index` field from tool calls
- OpenAI format requires `index` field restoration
- Parallel tool calls have model-specific limits

### Async Patterns
- Never use sync HTTP clients in async contexts
- Properly manage async context managers
- Handle timeouts and connection errors gracefully

### Development Server
- Use `uvicorn.reload=True` for development (not production)
- Poetry dependency management recommended
- Type checking catches most runtime errors early

## Debugging

### Logging
- Debug mode provides detailed request/response logging
- Logs include translation step details
- Error logs show original and translated formats

### Common Issues
- **Connection Refused**: VLLM server not running
- **Translation Errors**: Format incompatibility between models
- **Timeout Issues**: VLLM server overloaded or network problems

## Performance Considerations

### Throughput
- Target: 1000+ requests per second
- Async processing enables high concurrency
- Connection pooling reduces overhead

### Memory
- Low memory footprint (~50MB base)
- Scaling is linear with connection count
- No persistent data storage for privacy

## Security Notes

- Proxy doesn't store conversation data (in-memory only)
- Sensitive headers are filtered
- Authentication is planned but not yet implemented
- Consider rate limiting for production deployments

## Development Workflow

1. **Setup**: Install dependencies with Poetry/pip
2. **Configuration**: Copy `.env.example` to `.env` and configure
3. **Development**: Start proxy with `python devstral_proxy/main.py`
4. **Testing**: Run `python test_proxy.py` for quick validation
5. **Quality**: Use `black`, `isort`, and `mypy` before commits
6. **Deployment**: Use proper process management (systemd, etc.)

## Future Enhancements

Planned features that may impact development:
- Rate limiting and authentication
- Prometheus metrics integration
- Docker containerization
- Load balancing for horizontal scaling

This guide provides the essential information for working effectively with the Devstral Proxy codebase. Focus on async patterns, proper configuration, and understanding the translation layer when making changes.