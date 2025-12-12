#!/bin/bash
# Devstral Proxy Test Script

set -e

# Configuration
PROXY_URL="http://localhost:9000"
MODEL="devstral-small-2"
API_KEY="test-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ;;
        "warning")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "info")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
    esac
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            PROXY_URL="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --help)
            echo "Devstral Proxy Test Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --url URL        Proxy server URL (default: http://localhost:9000)"
            echo "  --model MODEL    Model name (default: devstral-small-2)"
            echo "  --api-key KEY   API key (default: test-key)"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "==========================================="
echo "Devstral Proxy Test Suite"
echo "==========================================="
echo "Proxy URL: $PROXY_URL"
echo "Model: $MODEL"
echo "==========================================="

# Test 1: Health Check
echo "Testing health check..."
if curl -s "$PROXY_URL/health" > /dev/null; then
    print_status "success" "Health check passed"
else
    print_status "error" "Health check failed - proxy not running?"
    exit 1
fi

# Test 2: Basic Chat Completion
echo "Testing basic chat completion..."
RESPONSE=$(curl -s -X POST \
    "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"Say 'Hello World'\"}
        ],
        \"max_tokens\": 50
    }")

if echo "$RESPONSE" | grep -q "content"; then
    print_status "success" "Basic chat completion passed"
    CONTENT=$(echo "$RESPONSE" | grep -o '"content":"[^"]*' | cut -d'"' -f4)
    print_status "info" "Response: $CONTENT"
else
    print_status "error" "Basic chat completion failed"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 3: Streaming Chat Completion
echo "Testing streaming chat completion..."
STREAM_RESPONSE=$(timeout 30s curl -s -X POST \
    "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"Count from 1 to 5\"}
        ],
        \"stream\": true,
        \"max_tokens\": 50
    }")

if echo "$STREAM_RESPONSE" | grep -q "data:"; then
    print_status "success" "Streaming chat completion passed"
    CHUNKS=$(echo "$STREAM_RESPONSE" | grep -c "data:" || echo "0")
    print_status "info" "Received $CHUNKS data chunks"
else
    print_status "warning" "Streaming test had issues"
    echo "Response: $STREAM_RESPONSE"
fi

# Test 4: Tool Calls
echo "Testing tool calls..."
TOOL_RESPONSE=$(curl -s -X POST \
    "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"What's the weather in San Francisco?\"}
        ],
        \"tools\": [
            {
                \"type\": \"function\",
                \"function\": {
                    \"name\": \"get_weather\",
                    \"description\": \"Get current weather\",
                    \"parameters\": {
                        \"type\": \"object\",
                        \"properties\": {
                            \"location\": {\"type\": \"string\"}
                        },
                        \"required\": [\"location\"]
                    }
                }
            }
        ],
        \"max_tokens\": 50
    }")

if echo "$TOOL_RESPONSE" | grep -q "tool_calls"; then
    print_status "success" "Tool calls passed"
    TOOL_NAME=$(echo "$TOOL_RESPONSE" | grep -o '"name":"get_weather"' | head -1)
    print_status "info" "Tool called: $TOOL_NAME"
else
    print_status "warning" "Tool calls test had issues"
    echo "Response: $TOOL_RESPONSE"
fi

# Test 5: Error Handling
echo "Testing error handling..."
ERROR_RESPONSE=$(curl -s -X POST \
    "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"invalid-model\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"Hello\"}
        ]
    }")

if echo "$ERROR_RESPONSE" | grep -q "error"; then
    print_status "success" "Error handling passed"
    ERROR_MSG=$(echo "$ERROR_RESPONSE" | grep -o '"message":"[^"]*' | cut -d'"' -f4 | head -1)
    print_status "info" "Error message: $ERROR_MSG"
else
    print_status "warning" "Error handling test unexpected"
    echo "Response: $ERROR_RESPONSE"
fi

# Test 6: Multiple Messages
echo "Testing multi-turn conversation..."
MULTI_RESPONSE=$(curl -s -X POST \
    "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"My name is Alice\"},
            {\"role\": \"assistant\", \"content\": \"Hello Alice! Nice to meet you.\"},
            {\"role\": \"user\", \"content\": \"What's my name?\"}
        ],
        \"max_tokens\": 50
    }")

if echo "$MULTI_RESPONSE" | grep -q "Alice"; then
    print_status "success" "Multi-turn conversation passed"
    print_status "info" "Context maintained correctly"
else
    print_status "warning" "Multi-turn conversation test had issues"
    echo "Response: $MULTI_RESPONSE"
fi

# Test 7: Performance Test
echo "Testing performance (5 concurrent requests)..."
for i in {1..5}; do
    (
        curl -s -X POST \
            "$PROXY_URL/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "{
                \"model\": \"$MODEL\",
                \"messages\": [
                    {\"role\": \"user\", \"content\": \"Respond with 'Request $i'\"}
                ],
                \"max_tokens\": 20
            }" > /dev/null
    ) &
done
wait

print_status "success" "Performance test completed"

# Test 8: Root Endpoint
echo "Testing root endpoint..."
ROOT_RESPONSE=$(curl -s "$PROXY_URL/")

if echo "$ROOT_RESPONSE" | grep -q "Devstral Proxy"; then
    print_status "success" "Root endpoint test passed"
    PROXY_VERSION=$(echo "$ROOT_RESPONSE" | grep -o '"version":"[^"]*' | cut -d'"' -f4)
    print_status "info" "Proxy version: $PROXY_VERSION"
else
    print_status "warning" "Root endpoint test had issues"
    echo "Response: $ROOT_RESPONSE"
fi

echo "==========================================="
echo "Test Suite Results"
echo "==========================================="
echo "All tests completed!"
echo ""
echo "For more detailed testing, run:"
echo "  python test_proxy.py"
echo "  python qa/run_tests.py"
echo ""
echo "For continuous integration, see:"
echo "  github.com/jefferson-nunn/devstral-proxy"
echo "==========================================="