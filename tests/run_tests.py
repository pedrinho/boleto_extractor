#!/usr/bin/env python3
"""
Test runner for boleto_extractor tests.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import boleto_extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_extractor import TestBoletoExtractor
from tests.test_cli import TestCLI


def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestBoletoExtractor))
    test_suite.addTest(unittest.makeSuite(TestCLI))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests()) 