# Devstral Proxy QA Test Suite

Comprehensive testing framework for the Devstral Proxy, covering logging, utility functions, VLLM integration, proxy functionality, tool calls, and end-to-end integration.

## 📋 Test Categories

### 1. **Logging Tests**
- Log file creation and permissions
- Log directory accessibility

### 2. **Utility Function Tests**
- OpenAI to Mistral message conversion
- Tool call handling and transformation
- Message validation and filtering

### 3. **VLLM Server Tests**
- Server reachability and connectivity
- Model availability (especially Devstral models)
- Health check endpoints

### 4. **Proxy Functionality Tests**
- Proxy initialization and configuration
- Model-specific settings retrieval
- Health check endpoints

### 5. **Tool Call Tests**
- Valid tool call validation
- Invalid tool call detection
- Tool call limit enforcement
- Error handling and responses

### 6. **Integration Tests**
- End-to-end request/response cycles
- Configuration consistency between VIBE and proxy
- System-wide compatibility checks

## 🚀 Running Tests

### Basic Test Run
```bash
cd /home/renter/devstral-proxy
python qa/run_tests.py
```

### Run Specific Test Categories
You can modify the `QATestSuite.run_all_tests()` method to run specific categories:

```python
# In qa/__init__.py, modify run_all_tests() to run only specific tests:
def run_all_tests(self):
    qa_logger.info("Starting QA test suite")
    
    # Run only VLLM and tool call tests
    self._run_vllm_tests()
    self._run_tool_call_tests()
    
    self._generate_report()
    return self.pass_count == self.test_count
```

## 📊 Test Reports

Test reports are automatically generated in JSON format and saved to:
```
qa/logs/qa_report_YYYYMMDD_HHMMSS.json
```

Each report contains:
- Test suite metadata (timestamps, duration)
- Total test count and pass/fail statistics
- Detailed results for each test
- Debug information for failed tests

## 🔧 Test Configuration

The test suite uses the same configuration as the main proxy. You can adjust settings in:

1. **Environment variables** (`.env` file)
2. **Proxy configuration** (`devstral_proxy/config.py`)
3. **VIBE configuration** (`~/.vibe/config.toml`)

## 🧪 Test Data

Test data and sample files are stored in:
```
qa/test_data/
```

You can add sample files here for testing file operations.

## 📈 Test Coverage

The test suite provides comprehensive coverage of:

| Component | Test Coverage |
|-----------|---------------|
| Logging | ✅ File creation, permissions |
| Utilities | ✅ Message conversion, validation |
| VLLM | ✅ Connectivity, model availability |
| Proxy | ✅ Initialization, configuration |
| Tool Calls | ✅ Validation, limits, error handling |
| Integration | ✅ End-to-end, config consistency |

## 🔄 Continuous Testing

For continuous testing, you can set up a cron job or systemd service:

### Cron Job Example
```bash
# Run tests every hour and log results
0 * * * * cd /home/renter/devstral-proxy && python qa/run_tests.py >> /var/log/devstral_qa_cron.log 2>&1
```

### Systemd Service Example
```ini
# /etc/systemd/system/devstral-qa.service
[Unit]
Description=Devstral Proxy QA Tests
After=network.target

[Service]
User=renter
WorkingDirectory=/home/renter/devstral-proxy
ExecStart=/usr/bin/python3 qa/run_tests.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 🐛 Debugging Failed Tests

If tests fail, check:

1. **QA Logs**: `qa/logs/qa_tests.log`
2. **Proxy Logs**: `/var/log/vllm-proxy.log`
3. **VLLM Logs**: Check VLLM server logs
4. **Test Reports**: Detailed JSON reports in `qa/logs/`

## 🎯 Test Development

To add new tests:

1. **Add test methods** to the `QATestSuite` class
2. **Follow the pattern** of existing test methods
3. **Use TestResult** for consistent reporting
4. **Add logging** for debugging

Example of adding a new test:

```python
def _run_new_feature_tests(self):
    """Test new feature"""
    qa_logger.info("Running new feature tests...")
    
    try:
        # Test logic here
        success = some_test_condition
        
        test_result = TestResult(
            "new_feature_test",
            success,
            "New feature works correctly" if success else "New feature failed",
            {"details": "Additional debug info"}
        )
    except Exception as e:
        test_result = TestResult(
            "new_feature_test",
            False,
            f"New feature test crashed: {str(e)}"
        )
    
    self.add_result(test_result)
```

Then call it from `run_all_tests()`:
```python
def run_all_tests(self):
    # ... existing test calls
    self._run_new_feature_tests()
    # ... rest of the method
```

## 📋 Requirements

- Python 3.8+
- Required packages (same as main proxy)
- VLLM server running (for VLLM tests)
- Proper file permissions for log directories

## 🔒 Security Notes

- Test suite runs with the same permissions as the proxy
- No sensitive data is logged in test reports
- Error details are sanitized before logging

## 📚 Documentation

- **Test Results**: Detailed JSON reports with timestamps
- **Logging**: Comprehensive debug and error logging
- **Configuration**: Uses same config as main proxy
- **Extensibility**: Easy to add new test categories

The QA test suite provides a robust foundation for ensuring the Devstral Proxy works correctly with VIBE CLI and local models like Devstral-Small-2.