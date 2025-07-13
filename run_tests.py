#!/usr/bin/env python3
"""
Test runner for the Conference Talks Tag Manager application.
"""
import unittest
import sys
import os

# Add the src directory to the path before any imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def run_tests():
    """Run all unit tests."""
    # Set PYTHONPATH environment variable for subprocess calls
    os.environ['PYTHONPATH'] = src_path
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)