#!/usr/bin/env python3
"""
Functional tests for APA API Sniffer v2
Tests runtime behavior and data collection patterns
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class FunctionalTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, condition, expected=True):
        """Record a test result"""
        passed = condition == expected
        status = "✅" if passed else "❌"
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        self.tests.append({
            "name": name,
            "passed": passed,
            "condition": condition,
            "expected": expected
        })
        print(f"{status} {name}")
        return passed
    
    def summary(self):
        print("\n" + "="*80)
        print(f"FUNCTIONAL TEST SUMMARY: {self.passed}/{self.passed + self.failed} passed")
        print("="*80)
        for test in self.tests:
            status = "✅" if test["passed"] else "❌"
            print(f"  {status} {test['name']}")
        print("="*80)
        return self.failed == 0


def test_capture_mode_structure():
    """Test CAPTURE_MODES structure"""
    from apa_api_sniffer_v2 import CAPTURE_MODES
    
    tests = FunctionalTests()
    
    print("\nTesting CAPTURE_MODES Structure:")
    print("-" * 80)
    
    # Test mode count
    tests.test("Total modes equals 11", len(CAPTURE_MODES), 11)
    
    # Test mode keys are strings 1-11
    mode_keys = set(CAPTURE_MODES.keys())
    tests.test("Mode keys are '1' through '11'", mode_keys, 
               {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"})
    
    # Test each mode has name, key, desc
    for mode_id, mode in CAPTURE_MODES.items():
        tests.test(f"Mode {mode_id} has 'name'", "name" in mode)
        tests.test(f"Mode {mode_id} has 'key'", "key" in mode)
        tests.test(f"Mode {mode_id} has 'desc'", "desc" in mode)
        
        # Check name is not empty
        if mode.get("name"):
            tests.test(f"Mode {mode_id} name is not empty", len(mode["name"]) > 0)
    
    # Test flag combinations
    print("\nTesting Flag Combinations:")
    print("-" * 80)
    
    # Mode 1: API only
    mode1_flags = CAPTURE_MODES["1"]
    tests.test("Mode 1: collect_apis True", mode1_flags.get("collect_apis"), True)
    tests.test("Mode 1: collect_network False", mode1_flags.get("collect_network"), False)
    
    # Mode 5: Network Analysis
    mode5_flags = CAPTURE_MODES["5"]
    tests.test("Mode 5: collect_network True", mode5_flags.get("collect_network"), True)
    tests.test("Mode 5: collect_apis False", mode5_flags.get("collect_apis"), False)
    
    # Mode 11: Everything
    mode11_flags = CAPTURE_MODES["11"]
    capture_flags = [
        "collect_apis", "collect_images", "collect_dom", "collect_network",
        "collect_client_intelligence", "collect_session_auth",
        "collect_page_behavior", "collect_content_extraction",
        "collect_advanced_tracking"
    ]
    for flag in capture_flags:
        tests.test(f"Mode 11: {flag} True", mode11_flags.get(flag), True)
    
    return tests.summary()


def test_mode_keys():
    """Test mode key uniqueness and naming"""
    from apa_api_sniffer_v2 import CAPTURE_MODES
    
    tests = FunctionalTests()
    
    print("\nTesting Mode Keys:")
    print("-" * 80)
    
    mode_keys = [mode.get("key") for mode in CAPTURE_MODES.values()]
    
    # All keys should be unique
    tests.test("All mode keys are unique", len(mode_keys), len(set(mode_keys)))
    
    # Check expected keys exist
    expected_keys = [
        "api_only", "api_screenshots", "api_images", "api_dom",
        "network_analysis", "client_intelligence", "session_auth",
        "page_behavior", "content_extraction", "advanced_tracking",
        "comprehensive"
    ]
    
    for expected_key in expected_keys:
        tests.test(f"Mode key '{expected_key}' exists", expected_key in mode_keys)
    
    return tests.summary()


def test_cli_descriptions():
    """Test CLI descriptions"""
    from apa_api_sniffer_v2 import CAPTURE_MODES
    
    tests = FunctionalTests()
    
    print("\nTesting CLI Descriptions:")
    print("-" * 80)
    
    for mode_id, mode in CAPTURE_MODES.items():
        desc = mode.get("desc", "")
        tests.test(f"Mode {mode_id} description is not empty", len(desc) > 0)
        tests.test(f"Mode {mode_id} description is reasonable", 
                   len(desc) > 5)  # At least some text
    
    return tests.summary()


def test_flag_consistency():
    """Test that all modes have consistent flag structures"""
    from apa_api_sniffer_v2 import CAPTURE_MODES
    
    tests = FunctionalTests()
    
    print("\nTesting Flag Consistency:")
    print("-" * 80)
    
    required_flags = [
        "collect_apis", "collect_images", "collect_dom", "collect_network",
        "collect_client_intelligence", "collect_session_auth",
        "collect_page_behavior", "collect_content_extraction",
        "collect_advanced_tracking"
    ]
    
    # Every mode should have all flags
    for mode_id, mode in CAPTURE_MODES.items():
        for flag in required_flags:
            tests.test(f"Mode {mode_id} has flag '{flag}'", flag in mode)
            tests.test(f"Mode {mode_id} flag '{flag}' is boolean", 
                       isinstance(mode.get(flag), bool))
    
    return tests.summary()


def test_mode_isolation():
    """Test that specialized modes have appropriate isolation"""
    from apa_api_sniffer_v2 import CAPTURE_MODES
    
    tests = FunctionalTests()
    
    print("\nTesting Mode Isolation:")
    print("-" * 80)
    
    # For modes 5-10, check that non-primary flags are False
    specialized_modes = {
        "5": "collect_network",
        "6": "collect_client_intelligence",
        "7": "collect_session_auth",
        "8": "collect_page_behavior",
        "9": "collect_content_extraction",
        "10": "collect_advanced_tracking",
    }
    
    for mode_id, primary_flag in specialized_modes.items():
        mode = CAPTURE_MODES[mode_id]
        
        # Primary flag should be True
        tests.test(f"Mode {mode_id}: {primary_flag} is True", 
                   mode.get(primary_flag), True)
        
        # All other capture flags should be False
        other_flags = [f for f in [
            "collect_apis", "collect_images", "collect_dom", "collect_network",
            "collect_client_intelligence", "collect_session_auth",
            "collect_page_behavior", "collect_content_extraction",
            "collect_advanced_tracking"
        ] if f != primary_flag]
        
        for flag in other_flags:
            tests.test(f"Mode {mode_id}: {flag} is False", 
                       mode.get(flag), False)
    
    return tests.summary()


def main():
    print("\n" + "="*80)
    print("APA API SNIFFER v2 - FUNCTIONAL TEST SUITE")
    print("="*80)
    
    all_passed = True
    
    all_passed &= test_capture_mode_structure()
    all_passed &= test_mode_keys()
    all_passed &= test_cli_descriptions()
    all_passed &= test_flag_consistency()
    all_passed &= test_mode_isolation()
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL FUNCTIONAL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80 + "\n")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
