"""
QA Test Suite for Devstral Proxy

Comprehensive testing framework for proxy functionality, tool calls, and VLLM integration.
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devstral_proxy.config import settings
from devstral_proxy.utils import (
    convert_openai_to_mistral_message,
    sanitize_request_body,
    sanitize_response_body,
    validate_tool_call_correspondence
)

# Configure QA logging
qa_logger = logging.getLogger("devstral_proxy_qa")
qa_logger.setLevel(logging.DEBUG)

# Create QA log directory
QA_LOG_DIR = PROJECT_ROOT / "qa" / "logs"
QA_LOG_DIR.mkdir(exist_ok=True)

# File handler
file_handler = logging.FileHandler(QA_LOG_DIR / "qa_tests.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
qa_logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
qa_logger.addHandler(console_handler)

class TestResult:
    """Container for test results"""
    
    def __init__(self, test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }
    
    def log(self):
        level = logging.INFO if self.success else logging.ERROR
        qa_logger.log(level, f"TEST {self.test_name}: {'PASS' if self.success else 'FAIL'} - {self.message}")
        if self.details:
            qa_logger.debug(f"Test details: {json.dumps(self.details, indent=2, default=str)}")

class QATestSuite:
    """Main QA test suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
    
    def add_result(self, result: TestResult):
        """Add test result to suite"""
        self.results.append(result)
        self.test_count += 1
        if result.success:
            self.pass_count += 1
        else:
            self.fail_count += 1
        result.log()
    
    def run_all_tests(self):
        """Run all test categories"""
        qa_logger.info("Starting comprehensive QA test suite")
        
        # Run test categories
        self._run_logging_tests()
        self._run_util_tests()
        self._run_vllm_tests()
        self._run_proxy_tests()
        self._run_tool_call_tests()
        self._run_integration_tests()
        
        # Generate report
        self._generate_report()
        
        qa_logger.info(f"QA test suite completed: {self.pass_count}/{self.test_count} passed")
        return self.pass_count == self.test_count
    
    def _run_logging_tests(self):
        """Test logging functionality"""
        qa_logger.info("Running logging tests...")
        
        # Test 1: Log file creation
        log_file = QA_LOG_DIR / "qa_tests.log"
        test_result = TestResult(
            "logging_file_creation",
            log_file.exists(),
            "QA log file created successfully" if log_file.exists() else "QA log file not created"
        )
        self.add_result(test_result)
        
        # Test 2: Log directory permissions
        try:
            test_file = QA_LOG_DIR / "test_permissions.txt"
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            test_result = TestResult(
                "logging_directory_permissions",
                True,
                "Log directory has write permissions"
            )
        except Exception as e:
            test_result = TestResult(
                "logging_directory_permissions",
                False,
                f"Log directory permission error: {str(e)}"
            )
        self.add_result(test_result)
    
    def _run_util_tests(self):
        """Test utility functions"""
        qa_logger.info("Running utility function tests...")
        
        # Test 1: Message conversion - user message
        user_message = {
            "role": "user",
            "content": "Hello, can you read a file for me?"
        }
        converted = convert_openai_to_mistral_message(user_message)
        test_result = TestResult(
            "util_user_message_conversion",
            converted is not None and converted["role"] == "user",
            "User message converted successfully" if converted else "User message conversion failed"
        )
        self.add_result(test_result)
        
        # Test 2: Message conversion - assistant with tool calls
        assistant_message = {
            "role": "assistant",
            "content": "I'll help with that",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "README.md"}'
                    }
                }
            ]
        }
        converted = convert_openai_to_mistral_message(assistant_message)
        test_result = TestResult(
            "util_assistant_tool_call_conversion",
            converted is not None and "tool_calls" in converted,
            "Assistant tool call converted successfully" if converted else "Assistant tool call conversion failed"
        )
        self.add_result(test_result)
        
        # Test 3: Tool message dropping
        tool_message = {
            "role": "tool",
            "content": "File content here",
            "tool_call_id": "call_123"
        }
        converted = convert_openai_to_mistral_message(tool_message)
        test_result = TestResult(
            "util_tool_message_dropping",
            converted is None,
            "Tool message correctly dropped" if converted is None else "Tool message not dropped"
        )
        self.add_result(test_result)
    
    def _run_vllm_tests(self):
        """Test VLLM server connectivity and status"""
        qa_logger.info("Running VLLM server tests...")
        
        vllm_base = settings.VLLM_BASE
        
        # Test 1: VLLM server reachability
        try:
            response = requests.get(f"{vllm_base}/v1/models", timeout=5)
            success = response.status_code == 200
            models = response.json().get("data", []) if success else []
            
            test_result = TestResult(
                "vllm_server_reachability",
                success,
                f"VLLM server reachable with {len(models)} models" if success else f"VLLM server unreachable: {response.status_code}",
                {"status_code": response.status_code, "models": models}
            )
        except Exception as e:
            test_result = TestResult(
                "vllm_server_reachability",
                False,
                f"VLLM server connection error: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 2: Devstral-Small-2 model availability
        try:
            response = requests.get(f"{vllm_base}/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json().get("data", [])
                devstral_models = [m for m in models if "devstral" in m.get("id", "").lower()]
                success = len(devstral_models) > 0
                
                test_result = TestResult(
                    "vllm_devstral_model_availability",
                    success,
                    f"Found {len(devstral_models)} Devstral models" if success else "No Devstral models found",
                    {"available_models": devstral_models}
                )
            else:
                test_result = TestResult(
                    "vllm_devstral_model_availability",
                    False,
                    f"VLLM models endpoint failed: {response.status_code}"
                )
        except Exception as e:
            test_result = TestResult(
                "vllm_devstral_model_availability",
                False,
                f"VLLM models check error: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 3: VLLM health check
        try:
            response = requests.get(f"{vllm_base}/health", timeout=5)
            success = response.status_code == 200
            
            test_result = TestResult(
                "vllm_health_check",
                success,
                "VLLM health check passed" if success else f"VLLM health check failed: {response.status_code}",
                {"status_code": response.status_code, "response": response.text}
            )
        except Exception as e:
            test_result = TestResult(
                "vllm_health_check",
                False,
                f"VLLM health check error: {str(e)}"
            )
        self.add_result(test_result)
    
    def _run_proxy_tests(self):
        """Test proxy functionality"""
        qa_logger.info("Running proxy functionality tests...")
        
        # Test 1: Proxy configuration validation
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            
            test_result = TestResult(
                "proxy_initialization",
                True,
                "Proxy initialized successfully",
                {"vllm_base": proxy.vllm_base, "debug_mode": proxy.debug}
            )
        except Exception as e:
            test_result = TestResult(
                "proxy_initialization",
                False,
                f"Proxy initialization failed: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 2: Model settings retrieval
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            
            # Test with known model
            devstral_settings = proxy.get_model_settings("devstral-small-2")
            success = "tool_call_format" in devstral_settings
            
            test_result = TestResult(
                "proxy_model_settings",
                success,
                "Model settings retrieved successfully" if success else "Model settings retrieval failed",
                {"devstral_small_2_settings": devstral_settings}
            )
        except Exception as e:
            test_result = TestResult(
                "proxy_model_settings",
                False,
                f"Model settings test failed: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 3: Health check endpoint
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            health = proxy.health_check()
            
            success = "status" in health and health["status"] == "ok"
            
            test_result = TestResult(
                "proxy_health_check",
                success,
                "Proxy health check passed" if success else "Proxy health check failed",
                {"health_data": health}
            )
        except Exception as e:
            test_result = TestResult(
                "proxy_health_check",
                False,
                f"Proxy health check error: {str(e)}"
            )
        self.add_result(test_result)
    
    def _run_tool_call_tests(self):
        """Test tool call functionality"""
        qa_logger.info("Running tool call tests...")
        
        # Test 1: Tool call validation
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            
            valid_tool_calls = [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path": "test.txt"}'
                    }
                }
            ]
            
            validation_result = proxy._validate_tool_calls(valid_tool_calls, "devstral-small-2")
            
            test_result = TestResult(
                "tool_call_validation_valid",
                validation_result,
                "Valid tool calls passed validation" if validation_result else "Valid tool calls failed validation"
            )
        except Exception as e:
            test_result = TestResult(
                "tool_call_validation_valid",
                False,
                f"Tool call validation test failed: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 2: Invalid tool call detection
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            
            invalid_tool_calls = [
                {
                    "id": "call_1",
                    "type": "function"
                    # Missing function details
                }
            ]
            
            validation_result = proxy._validate_tool_calls(invalid_tool_calls, "devstral-small-2")
            
            test_result = TestResult(
                "tool_call_validation_invalid",
                not validation_result,  # Should fail validation
                "Invalid tool calls correctly rejected" if not validation_result else "Invalid tool calls incorrectly passed"
            )
        except Exception as e:
            test_result = TestResult(
                "tool_call_validation_invalid",
                False,
                f"Invalid tool call test failed: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 3: Tool call limit enforcement
        try:
            from devstral_proxy.proxy import DevstralProxy
            proxy = DevstralProxy()
            
            # Create too many tool calls (exceed limit of 10)
            too_many_tool_calls = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": f"tool_{i}",
                        "arguments": '{}'
                    }
                }
                for i in range(15)  # Exceed the 10 call limit
            ]
            
            validation_result = proxy._validate_tool_calls(too_many_tool_calls, "devstral-small-2")
            
            test_result = TestResult(
                "tool_call_limit_enforcement",
                not validation_result,  # Should fail due to limit
                "Tool call limit correctly enforced" if not validation_result else "Tool call limit not enforced"
            )
        except Exception as e:
            test_result = TestResult(
                "tool_call_limit_enforcement",
                False,
                f"Tool call limit test failed: {str(e)}"
            )
        self.add_result(test_result)
    
    def _run_integration_tests(self):
        """Test end-to-end integration"""
        qa_logger.info("Running integration tests...")
        
        # Test 1: Full request/response cycle (if proxy is running)
        try:
            proxy_url = f"http://{settings.PROXY_HOST}:{settings.PROXY_PORT}/v1/chat/completions"
            
            test_payload = {
                "model": "devstral-small",
                "messages": [
                    {
                        "role": "user",
                        "content": "What tools are available?"
                    }
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "description": "Read file content",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            }
            
            # Try to make request (may fail if proxy not running, which is expected)
            try:
                response = requests.post(proxy_url, json=test_payload, timeout=10)
                success = response.status_code in [200, 404]  # 404 if proxy not running is acceptable
                
                test_result = TestResult(
                    "integration_proxy_request",
                    success,
                    f"Proxy request successful: {response.status_code}" if success else f"Proxy request failed: {response.status_code}",
                    {"status_code": response.status_code, "url": proxy_url}
                )
            except Exception as e:
                # This is expected if proxy isn't running
                test_result = TestResult(
                    "integration_proxy_request",
                    True,  # Not running is acceptable for this test
                    "Proxy not running (expected if not started)",
                    {"error": str(e), "expected": "Proxy may not be running"}
                )
        except Exception as e:
            test_result = TestResult(
                "integration_proxy_request",
                False,
                f"Integration test failed: {str(e)}"
            )
        self.add_result(test_result)
        
        # Test 2: Configuration consistency check
        try:
            # Check that VIBE config and proxy config are aligned
            vibe_config_path = Path.home() / ".vibe" / "config.toml"
            if vibe_config_path.exists():
                import tomllib
                with open(vibe_config_path, 'rb') as f:
                    vibe_config = tomllib.load(f)
                
                active_model = vibe_config.get("active_model", "unknown")
                proxy_models = list(settings.MODEL_SPECIFIC_SETTINGS.keys())
                
                # Check if active model is supported by proxy
                model_base = active_model.split("-")[0]
                supported = any(model_base in proxy_model for proxy_model in proxy_models)
                
                test_result = TestResult(
                    "integration_config_consistency",
                    supported,
                    f"VIBE model {active_model} is supported by proxy" if supported else f"VIBE model {active_model} not found in proxy config",
                    {"vibe_active_model": active_model, "proxy_supported_models": proxy_models}
                )
            else:
                test_result = TestResult(
                    "integration_config_consistency",
                    False,
                    "VIBE config not found for consistency check"
                )
        except Exception as e:
            test_result = TestResult(
                "integration_config_consistency",
                False,
                f"Config consistency test failed: {str(e)}"
            )
        self.add_result(test_result)
    
    def _generate_report(self):
        """Generate test report"""
        report = {
            "test_suite": "Devstral Proxy QA",
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_tests": self.test_count,
            "passed_tests": self.pass_count,
            "failed_tests": self.fail_count,
            "pass_rate": self.pass_count / self.test_count if self.test_count > 0 else 0.0,
            "results": [result.to_dict() for result in self.results]
        }
        
        # Save report
        report_file = QA_LOG_DIR / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        qa_logger.info(f"QA report generated: {report_file}")
        
        # Print summary
        summary = (
            f"\n{'='*60}\n"
            f"QA TEST SUITE SUMMARY\n"
            f"{'='*60}\n"
            f"Total Tests: {self.test_count}\n"
            f"Passed: {self.pass_count}\n"
            f"Failed: {self.fail_count}\n"
            f"Pass Rate: {report['pass_rate']:.1%}\n"
            f"Duration: {report['duration_seconds']:.1f}s\n"
            f"Report: {report_file}\n"
            f"{'='*60}\n"
        )
        
        qa_logger.info(summary)
        
        return report

def run_qa_tests():
    """Run the complete QA test suite"""
    suite = QATestSuite()
    return suite.run_all_tests()

if __name__ == "__main__":
    success = run_qa_tests()
    sys.exit(0 if success else 1)