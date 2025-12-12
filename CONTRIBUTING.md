# Contributing to Devstral Proxy

Thank you for your interest in contributing to the Devstral Proxy project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Poetry (recommended) or pip
- Git

### Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/devstral-proxy.git
   cd devstral-proxy
   ```

2. **Install dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   poetry shell
   
   # Using pip
   pip install -e .
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run tests**
   ```bash
   python test_proxy.py
   python qa/run_tests.py
   ```

## 📝 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow the code style guidelines (Black + isort + mypy)
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Quick functional tests
python test_proxy.py

# Comprehensive QA tests
python qa/run_tests.py

# Unit tests
pytest tests/ -v
```

### 4. Code Quality

```bash
# Format code
black devstral_proxy/

# Sort imports
isort devstral_proxy/

# Type checking
mypy devstral_proxy/
```

### 5. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new feature description"
# or
git commit -m "fix: resolve issue description"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a Pull Request with:
- Clear description of changes
- Testing performed
- Any breaking changes

## 🧪 Testing

### Test Types

- **Functional Tests**: `test_proxy.py` - End-to-end functionality
- **QA Suite**: `qa/run_tests.py` - Comprehensive testing
- **Unit Tests**: `tests/` directory - Component testing

### Writing Tests

```python
import pytest
import httpx
from devstral_proxy.main import app

@pytest.mark.asyncio
async def test_your_feature():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", json={...})
        assert response.status_code == 200
```

## 📚 Documentation

- Update README.md for user-facing changes
- Add inline docstrings for new functions
- Update AGENTS.md for development-related changes

## 🏗️ Architecture

### Key Components

- **Proxy Server** (`main.py`): FastAPI application
- **Translation Layer** (`proxy.py`): OpenAI ↔ Mistral conversion
- **Data Models** (`models.py`): Pydantic schemas
- **Configuration** (`config.py`): Settings management
- **Utilities** (`utils.py`): Helper functions

### Adding New Features

1. **New Endpoints**: Add to `main.py`
2. **Translation Logic**: Add to `proxy.py`
3. **Data Structures**: Add to `models.py`
4. **Configuration**: Add to `config.py`
5. **Tests**: Add to `test_proxy.py` or `tests/`

## 🎯 Code Style

### Formatting

```bash
# Line length: 88 characters
# Use Black for formatting
# Use isort for import sorting
```

### Type Hints

```python
from typing import Dict, Any, Optional

def process_data(data: Dict[str, Any]) -> Optional[str]:
    """Process data and return result."""
    return data.get("processed")
```

### Documentation

```python
def translate_request(request: OpenAIRequest) -> MistralRequest:
    """
    Translate OpenAI request to Mistral format.
    
    Args:
        request: OpenAI-format request
        
    Returns:
        Mistral-format request
    """
```

## 🐛 Bug Reports

When reporting bugs, include:

1. Environment details (Python version, OS)
2. Configuration used
3. Steps to reproduce
4. Expected vs actual behavior
5. Logs (if applicable)

## 💡 Feature Requests

For feature requests:

1. Describe the use case
2. Explain why it's valuable
3. Consider implementation approach
4. Discuss breaking changes

## 🔍 Review Process

All PRs go through:

1. **Automated Tests**: Must pass all tests
2. **Code Quality**: Must pass linting and type checking
3. **Review**: At least one maintainer review
4. **Documentation**: Docs updated if needed

## 📋 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Update documentation

## 🤝 Community

- Be respectful and constructive
- Help others in issues and discussions
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

## 📞 Getting Help

- Check [AGENTS.md](AGENTS.md) for development guide
- Review existing issues and PRs
- Ask questions in discussions or issues

---

Thank you for contributing to the Devstral Proxy project! 🎉