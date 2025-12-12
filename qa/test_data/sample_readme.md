# Sample README for Testing

This is a sample README file used for testing the Devstral Proxy QA test suite.

## Features

- **Tool Call Testing**: Test read_file, write_file, search_replace operations
- **Message Conversion**: Test OpenAI to Mistral format conversion
- **Error Handling**: Test validation and error responses
- **Integration Testing**: Test end-to-end proxy functionality

## Usage

This file is used by the QA test suite to verify file operations work correctly.

## Test Scenarios

1. **File Reading**: Verify read_file tool can access this file
2. **Content Validation**: Verify file content is preserved during operations
3. **Error Handling**: Test permission errors and file not found scenarios

## Expected Results

- ✅ File should be readable by the proxy
- ✅ Content should match expected format
- ✅ File operations should be logged properly
- ✅ Error handling should work for invalid paths

This file helps ensure the Devstral Proxy handles file operations correctly when working with VIBE CLI and local models like Devstral-Small-2.