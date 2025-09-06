#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for Tetris Enhanced
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

def run_tests():
    """Run all tests for the Tetris Enhanced project."""
    print("Running tests for Tetris Enhanced...")
    
    try:
        # Run the test framework
        from tests.test_framework import run_all_tests
        success = run_all_tests()
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())