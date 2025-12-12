#!/usr/bin/env python3
"""
QA Test Runner for Devstral Proxy

Simple script to run the comprehensive QA test suite.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from qa import run_qa_tests

def main():
    """Main test runner"""
    print("🧪 Devstral Proxy QA Test Suite")
    print("=" * 50)
    
    try:
        success = run_qa_tests()
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())