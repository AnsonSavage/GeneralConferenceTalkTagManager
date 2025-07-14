#!/usr/bin/env python3
"""
Test runner for the Conference Talks Tag Manager application.
Supports both unit tests and integration tests.
"""
import unittest
import sys
import os
import argparse

# Add the src directory to the path before any imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running Unit Tests")
    print("=" * 40)
    
    # Set PYTHONPATH environment variable for subprocess calls
    os.environ['PYTHONPATH'] = src_path
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests', 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run all integration tests."""
    print("\n🔗 Running Integration Tests")
    print("=" * 40)
    
    # Import the integration test runner
    integration_dir = os.path.join(os.path.dirname(__file__), 'tests', 'integration')
    sys.path.insert(0, integration_dir)
    
    try:
        # Import and run both integration tests with correct class names
        from test_standalone_workflow import SimpleWorkflowIntegrationTest
        from test_database_merge import SimpleDatabaseMergeTest
        
        passed = 0
        failed = 0
        
        # Run standalone workflow test
        print("Running Simple Workflow Integration Test...")
        workflow_test = SimpleWorkflowIntegrationTest()
        workflow_success = workflow_test.run_test()
        
        if workflow_success:
            print("✅ Simple Workflow Integration Test: PASSED")
            passed += 1
        else:
            print("❌ Simple Workflow Integration Test: FAILED")
            failed += 1
            
        # Run database merge test
        print("\nRunning Database Merge Integration Test...")
        merge_test = SimpleDatabaseMergeTest()
        merge_success = merge_test.run_test()
        
        if merge_success:
            print("✅ Database Merge Integration Test: PASSED")
            passed += 1
        else:
            print("❌ Database Merge Integration Test: FAILED")
            failed += 1
            
        print(f"\n📊 Integration Test Summary: {passed} passed, {failed} failed")
        return failed == 0
        
    except ImportError as e:
        print(f"❌ Failed to import integration tests: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_all_tests():
    """Run both unit and integration tests."""
    print("🚀 Running Complete Test Suite")
    print("=" * 60)
    
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 60)
    
    if unit_success:
        print("✅ Unit Tests: PASSED")
    else:
        print("❌ Unit Tests: FAILED")
        
    if integration_success:
        print("✅ Integration Tests: PASSED")
    else:
        print("❌ Integration Tests: FAILED")
    
    overall_success = unit_success and integration_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n💥 SOME TESTS FAILED!")
        
    return overall_success

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description='Run tests for Conference Talks Tag Manager')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific option is provided
    if not args.unit and not args.integration:
        args.all = True
    
    success = True
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.all:
        success = run_all_tests()
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())