#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for Tetris Enhanced
"""

import sys
import os
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the project root to the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Remove any conflicting 'tests' module from sys.modules
if 'tests' in sys.modules:
    del sys.modules['tests']

def run_tests():
    """Run all tests for the Tetris Enhanced project."""
    print("Running tests for Tetris Enhanced...")

    try:
        # Run the test framework - use explicit path to avoid conflicts
        test_framework_path = os.path.join(PROJECT_ROOT, 'tests', 'test_framework.py')
        spec = __import__('importlib.util').util.spec_from_file_location(
            "test_framework", test_framework_path
        )
        test_module = __import__('importlib.util').util.module_from_spec(spec)
        sys.modules['test_framework'] = test_module
        spec.loader.exec_module(test_module)
        
        success = test_module.run_all_tests()

        if success:
            print("\n[PASS] All tests passed!")
            return 0
        else:
            print("\n[FAIL] Some tests failed!")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())