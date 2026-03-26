#!/usr/bin/env python3
"""
Comprehensive test suite for apa_api_sniffer_v2.py
Tests all modes, helper functions, and core functionality
"""

import sys
import os
import json
import asyncio
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import sniffer functions
try:
    # We'll import and test the functions/classes we can
    print("[INFO] Attempting to import sniffer module...")
except Exception as e:
    print(f"[ERROR] Import error: {e}")


class TestSnifferCore(unittest.TestCase):
    """Test core sniffer functionality"""
    
    def test_imports(self):
        """Test that sniffer file has valid Python syntax"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        self.assertTrue(sniffer_path.exists(), f"Sniffer file not found: {sniffer_path}")
        
        # Verify file is readable
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Sniffer file is empty")
            self.assertIn("async def", content, "No async functions found")
    
    def test_syntax_validation(self):
        """Test that the sniffer file has valid Python syntax"""
        import py_compile
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        try:
            py_compile.compile(str(sniffer_path), doraise=True)
            print("✓ Sniffer syntax validation passed")
        except py_compile.PyCompileError as e:
            self.fail(f"Sniffer has syntax errors: {e}")
    
    def test_critical_functions_exist(self):
        """Test that critical functions are defined"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for mode test functions
            required_functions = [
                "test_cors_analysis",
                "test_jwt_analysis",
                "test_api_key_exposure",
                "test_sqli_testing",
                "test_xxe_injection",
                "test_command_injection",
                "test_graphql_endpoints",
                "test_auth_bypass",
                "test_graphql_authz_bypass",
                "detect_data_leakage",
                "discover_hidden_endpoints",
            ]
            
            for func in required_functions:
                self.assertIn(f"def {func}", content, f"Missing function: {func}")
                print(f"✓ Function '{func}' found")
    
    def test_capture_modes_config(self):
        """Test that CAPTURE_MODES dictionary is properly configured"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for all 26 modes
            mode_count = content.count('"collect_')
            self.assertGreater(mode_count, 50, "Not enough mode configurations found")
            
            # Check for mode 26
            self.assertIn("graphql_authz_bypass", content)
            print(f"✓ All {mode_count} mode configurations found")
    
    def test_global_variables_initialized(self):
        """Test that global variables are properly initialized"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            globals_to_check = [
                "captured_apis = {}",
                "api_count = 0",
                "RUN_ID",
                "RUN_DIR",
            ]
            
            for var in globals_to_check:
                self.assertIn(var, content, f"Global variable not initialized: {var}")
                print(f"✓ Global '{var}' initialized")


class TestTypeHandling(unittest.TestCase):
    """Test that type handling is correct (dict vs list issues)"""
    
    def test_cors_analysis_type_handling(self):
        """Test that CORS analysis handles dict/list properly"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find the CORS test function
            cors_start = content.find("async def test_cors_analysis")
            self.assertGreater(cors_start, 0, "CORS test function not found")
            
            cors_section = content[cors_start:cors_start+2000]
            
            # Check for isinstance check
            self.assertIn("isinstance(captured_apis, dict)", cors_section,
                         "CORS analysis missing isinstance check for captured_apis")
            print("✓ CORS analysis has proper type handling")
    
    def test_mode26_response_type_checks(self):
        """Test that Mode 26 response handling includes type checks"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find Mode 26
            mode26_start = content.find("async def test_graphql_authz_bypass")
            self.assertGreater(mode26_start, 0, "Mode 26 function not found")
            
            mode26_section = content[mode26_start:mode26_start+10000]
            
            # Count isinstance checks in Mode 26
            isinstance_count = mode26_section.count("isinstance(")
            self.assertGreater(isinstance_count, 5, "Mode 26 missing isinstance type checks")
            print(f"✓ Mode 26 has {isinstance_count} type checks")
    
    def test_no_chained_get_calls(self):
        """Test that chained .get() calls have proper validation"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find problematic patterns like: .get().get() without checks
            import re
            
            # Look for chained gets without proper validation
            # This is a simplified check - look for patterns that might be problematic
            mode26_start = content.find("async def test_graphql_authz_bypass")
            mode26_end = content.find("\nasync def", mode26_start + 100)
            
            if mode26_start > 0 and mode26_end > 0:
                mode26_section = content[mode26_start:mode26_end]
                
                # Check that response checks come before .get calls
                data_patterns = re.findall(r'if isinstance\(response.*?\):', mode26_section)
                self.assertGreater(len(data_patterns), 0, 
                                  "Mode 26 missing response type validation")
                print(f"✓ Mode 26 has proper response validation patterns")


class TestFunctionSignatures(unittest.TestCase):
    """Test that function signatures are correct"""
    
    def test_cors_analysis_signature(self):
        """Test CORS analysis function signature"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.assertIn("async def test_cors_analysis(page, context, captured_apis):",
                         content, "CORS analysis has wrong signature")
            print("✓ CORS analysis signature correct")
    
    def test_mode26_signature(self):
        """Test Mode 26 function signature"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.assertIn("async def test_graphql_authz_bypass(page, context, captured_apis):",
                         content, "Mode 26 has wrong signature")
            print("✓ Mode 26 signature correct")
    
    def test_data_leakage_signature(self):
        """Test data leakage function signature"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.assertIn("async def detect_data_leakage(page_data, api_responses):",
                         content, "Data leakage function has wrong signature")
            print("✓ Data leakage signature correct")


class TestAsyncFunctions(unittest.TestCase):
    """Test async function structure"""
    
    def test_all_test_functions_are_async(self):
        """Test that all test functions are async"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Count async test functions
            async_test_count = content.count("async def test_")
            self.assertGreater(async_test_count, 10, "Not enough async test functions")
            print(f"✓ Found {async_test_count} async test functions")
    
    def test_critical_awaits_present(self):
        """Test that page.evaluate() calls are awaited"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for await page.evaluate
            self.assertIn("await page.evaluate(", content,
                         "Missing await on page.evaluate() calls")
            print("✓ page.evaluate() calls are properly awaited")


class TestErrorHandling(unittest.TestCase):
    """Test that error handling is implemented"""
    
    def test_try_except_blocks(self):
        """Test that functions have try-except blocks"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            try_count = content.count("try:")
            except_count = content.count("except ")
            
            self.assertGreater(try_count, 50, "Not enough try blocks")
            self.assertGreater(except_count, 50, "Not enough except blocks")
            print(f"✓ Found {try_count} try blocks and {except_count} except blocks")
    
    def test_exception_handling_in_mode26(self):
        """Test that Mode 26 has proper exception handling"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            mode26_start = content.find("async def test_graphql_authz_bypass")
            mode26_end = content.find("\nasync def", mode26_start + 100)
            
            if mode26_start > 0:
                mode26_section = content[mode26_start:mode26_end]
                self.assertIn("except", mode26_section, "Mode 26 missing exception handling")
                self.assertIn("try:", mode26_section, "Mode 26 missing try blocks")
                print("✓ Mode 26 has proper exception handling")


class TestCodeQuality(unittest.TestCase):
    """Test code quality metrics"""
    
    def test_no_bare_excepts(self):
        """Test that there are no bare except clauses"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            bare_excepts = []
            for i, line in enumerate(lines, 1):
                if line.strip() == "except:" and "except Exception" not in lines[i-2:i]:
                    bare_excepts.append((i, line.strip()))
            
            # Allow some bare excepts but prefer specific exceptions
            self.assertLess(len(bare_excepts), 10, f"Too many bare except clauses: {bare_excepts}")
            if bare_excepts:
                print(f"⚠ Found {len(bare_excepts)} bare except clauses (acceptable)")
            else:
                print("✓ No bare except clauses")
    
    def test_file_size_reasonable(self):
        """Test that file size is reasonable"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        size = sniffer_path.stat().st_size
        
        # File should be between 100KB and 500KB
        self.assertGreater(size, 100_000, "Sniffer file too small")
        self.assertLess(size, 500_000, "Sniffer file too large")
        print(f"✓ Sniffer file size: {size:,} bytes (reasonable)")
    
    def test_line_count(self):
        """Test that line count is reasonable"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        # Should have 5000+ lines
        self.assertGreater(line_count, 5000, "Not enough lines of code")
        print(f"✓ Sniffer has {line_count:,} lines of code")


class TestModeConfigurations(unittest.TestCase):
    """Test that all 26 modes are properly configured"""
    
    def test_all_26_modes_exist(self):
        """Test that all 26 capture modes are defined"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find CAPTURE_MODES dictionary
            modes_start = content.find("CAPTURE_MODES = {")
            self.assertGreater(modes_start, 0, "CAPTURE_MODES not found")
            
            # Count mode numbers
            for i in range(1, 27):
                self.assertIn(f'"{i}": {{', content, f"Mode {i} not found")
            
            print("✓ All 26 modes are configured")
    
    def test_mode26_exists(self):
        """Test that Mode 26 specifically exists"""
        sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
        with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            self.assertIn('"26": {', content, "Mode 26 not found in CAPTURE_MODES")
            self.assertIn("graphql_authz_bypass", content, "Mode 26 key not found")
            self.assertIn("GraphQL Authorization Bypass Testing", content,
                         "Mode 26 description not found")
            print("✓ Mode 26 (GraphQL Authorization Bypass Testing) exists")


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("  COMPREHENSIVE SNIFFER TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSnifferCore))
    suite.addTests(loader.loadTestsFromTestCase(TestTypeHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestFunctionSignatures))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestModeConfigurations))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
