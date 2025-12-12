# Installation Guide

This guide will help you install and set up the Devstral Proxy on your system.

## Prerequisites

- Python 3.8 or higher
- pip or Poetry package manager
- Access to a Mistral/VLLM server
- (Optional) Git for cloning the repository

## Installation Methods

### Method 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/jefferson-nunn/devstral-proxy.git
cd devstral-proxy

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Verify installation
python -c "import devstral_proxy; print('Installation successful!')"
```

### Method 2: Using pip

```bash
# Clone the repository
git clone https://github.com/jefferson-nunn/devstral-proxy.git
cd devstral-proxy

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
python -c "import devstral_proxy; print('Installation successful!')"
```

### Method 3: Direct Installation from GitHub

```bash
# Using pip
pip install git+https://github.com/jefferson-nunn/devstral-proxy.git

# Using Poetry (if available)
poetry add git+https://github.com/jefferson-nunn/devstral-proxy.git
```

## Configuration

### 1. Environment Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

### 2. Configure VLLM Server

Edit `.env` with your VLLM server configuration:

```env
# VLLM Server Configuration
VLLM_BASE=http://127.0.0.1:8000

# Proxy Server Configuration
PROXY_HOST=0.0.0.0
PROXY_PORT=9000

# Debug and Logging
DEBUG=false
LOG_LEVEL=info
LOG_FILE=/var/log/vllm-proxy.log
```

### 3. Model Configuration

The proxy supports multiple Devstral models. Ensure your VLLM server is running with one of these models:

- `devstral-small-2`
- `devstral-small`
- `devstral-2`

## Startup

### Method 1: Direct Execution

```bash
# Using Poetry
poetry run python devstral_proxy/main.py

# Using pip/venv
python devstral_proxy/main.py
```

### Method 2: Module Execution

```bash
# Using Poetry
poetry run python -m devstral_proxy.main

# Using pip/venv
python -m devstral_proxy.main
```

### Method 3: Development Server

Enable auto-reload for development:

```bash
# Using Poetry
poetry run python -m devstral_proxy.main --reload

# Using pip/venv
python -m devstral_proxy.main --reload
```

## Verification

1. **Check Health Endpoint**

```bash
curl http://localhost:9000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vllm_status": "connected",
  "uptime": "0h 0m 30s"
}
```

2. **Test Chat Completions**

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "devstral-small-2",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

3. **Run Test Suite**

```bash
# Quick functional tests
python test_proxy.py

# Comprehensive QA tests
python qa/run_tests.py
```

## System Service Setup

### systemd (Linux)

Create a service file:

```bash
sudo nano /etc/systemd/system/devstral-proxy.service
```

```ini
[Unit]
Description=Devstral Proxy
After=network.target

[Service]
Type=user
WorkingDirectory=/path/to/devstral-proxy
Environment=PATH=/path/to/devstral-proxy/.venv/bin
ExecStart=/path/to/devstral-proxy/.venv/bin/python devstral_proxy/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable devstral-proxy
sudo systemctl start devstral-proxy
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install -e .

EXPOSE 9000

CMD ["python", "devstral_proxy/main.py"]
```

Build and run:

```bash
docker build -t devstral-proxy .
docker run -d -p 9000:9000 devstral-proxy
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**

```bash
# Check what's using the port
netstat -tulpn | grep :9000

# Change port in .env
PROXY_PORT=9001
```

2. **VLLM Connection Failed**

```bash
# Check if VLLM server is running
curl http://localhost:8000/health

# Verify VLLM URL in .env
VLLM_BASE=http://127.0.0.1:8000
```

3. **Import Errors**

```bash
# Verify installation
python -c "import devstral_proxy"

# Reinstall if needed
pip install -e .
```

4. **Permission Issues**

```bash
# Check directory permissions
ls -la /var/log/

# Change log directory if needed
LOG_FILE=./proxy.log
```

### Debug Mode

Enable debug logging for troubleshooting:

```env
DEBUG=true
LOG_LEVEL=debug
```

### Health Check

Monitor the proxy status:

```bash
# Health endpoint
curl http://localhost:9000/health

# Check logs
tail -f /var/log/vllm-proxy.log
```

## Performance Tuning

### Environment Variables

```env
# Worker threads (for production deployment)
WORKER_THREADS=4

# Request timeouts
REQUEST_TIMEOUT=30

# Connection pooling
MAX_CONNECTIONS=100
```

### Resource Monitoring

```bash
# Monitor CPU usage
top -p $(pgrep -f "devstral_proxy")

# Monitor memory usage
ps aux | grep devstral_proxy

# Monitor network connections
netstat -an | grep :9000
```

## Next Steps

After installation:

1. Read the [API Reference](API_REFERENCE.md) for usage examples
2. Check the [Contributing Guide](CONTRIBUTING.md) for development
3. Review the [Developer Guide](AGENTS.md) for internals
4. Set up monitoring and logging for production use

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [GitHub Issues](https://github.com/jefferson-nunn/devstral-proxy/issues)
3. Create a new issue with detailed information
4. Join our discussions for community support

---

Happy proxying! 🚀