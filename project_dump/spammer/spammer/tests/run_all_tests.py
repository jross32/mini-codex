#!/usr/bin/env python3
"""
Test runner - executes all test suites and reports results
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            cwd=str(Path(__file__).parent)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  SNIFFER COMPREHENSIVE TEST SUITE")
    print("  Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    tests_dir = Path(__file__).parent
    results = {}
    
    # Test 1: Syntax validation
    print("\n" + "="*70)
    print("  SYNTAX VALIDATION")
    print("="*70 + "\n")
    
    sniffer_path = tests_dir.parent / "apa_api_sniffer_v2.py"
    try:
        import py_compile
        py_compile.compile(str(sniffer_path), doraise=True)
        print("[OK] Syntax validation PASSED")
        results["Syntax Validation"] = True
    except Exception as e:
        print(f"[FAIL] Syntax validation FAILED: {e}")
        results["Syntax Validation"] = False
    
    # Test 2: Main test suite
    test_sniffer_path = tests_dir / "test_sniffer.py"
    if test_sniffer_path.exists():
        success = run_command(
            f"python test_sniffer.py",
            "RUNNING MAIN TEST SUITE"
        )
        results["Main Test Suite"] = success
    else:
        print(f"⚠️  test_sniffer.py not found")
        results["Main Test Suite"] = False
    
    # Test 3: Mode tests
    test_modes_path = tests_dir / "test_modes.py"
    if test_modes_path.exists():
        success = run_command(
            f"python test_modes.py",
            "RUNNING MODE CONFIGURATION TESTS"
        )
        results["Mode Tests"] = success
    else:
        print(f"⚠️  test_modes.py not found")
        results["Mode Tests"] = False
    
    # Summary
    print("\n" + "="*70)
    print("  FINAL TEST SUMMARY")
    print("="*70)
    
    for test_name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} test groups passed")
    
    if total_passed == total_tests:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[WARNING] {total_tests - total_passed} test group(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
