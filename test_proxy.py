#!/usr/bin/env python3
"""
Simple test script for Devstral Proxy
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:9000/health", timeout=5.0)
            data = response.json()
            
            print(f"✅ Health check successful!")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Uptime: {data.get('uptime')}")
            print(f"   VLLM Target: {data.get('vllm_target')}")
            return True
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False


async def test_chat_completion():
    """Test chat completion endpoint"""
    print("\n🔍 Testing chat completion endpoint...")
    
    test_message = {
        "model": "devstral-small-2",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            start_time = datetime.now()
            response = await client.post(
                "http://localhost:9000/v1/chat/completions",
                json=test_message,
                timeout=30.0
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chat completion successful!")
                print(f"   Response time: {duration:.3f}s")
                print(f"   Model: {data.get('model')}")
                print(f"   Choices: {len(data.get('choices', []))}")
                if data.get('choices'):
                    content = data['choices'][0]['message']['content']
                    print(f"   Content: {content[:100]}...")
                return True
            else:
                print(f"❌ Chat completion failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat completion failed: {e}")
            return False


async def test_tool_calls():
    """Test tool call functionality"""
    print("\n🔍 Testing tool call functionality...")
    
    test_message = {
        "model": "devstral-small-2",
        "messages": [
            {"role": "user", "content": "What's the weather in Paris?"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to get weather for"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:9000/v1/chat/completions",
                json=test_message,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Tool call test successful!")
                print(f"   Has tool calls: {'tool_calls' in data.get('choices', [{}])[0].get('message', {})}")
                return True
            else:
                print(f"❌ Tool call test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Tool call test failed: {e}")
            return False


async def main():
    """Run all tests"""
    print("🧪 Devstral Proxy Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test health endpoint
    results.append(await test_health())
    
    # Test chat completion
    results.append(await test_chat_completion())
    
    # Test tool calls
    results.append(await test_tool_calls())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print(f"   Passed: {sum(results)}/{len(results)}")
    print(f"   Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Proxy is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the proxy configuration.")
    
    return all(results)


if __name__ == "__main__":
    asyncio.run(main())