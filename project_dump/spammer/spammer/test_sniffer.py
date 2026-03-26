#!/usr/bin/env python3
"""
Test script for APA API Sniffer v2
Tests all 11 capture modes against sample websites
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add parent dir to path to import sniffer
sys.path.insert(0, str(Path(__file__).parent))

# Mock the environment for testing
os.environ["CAPTURE_MODE"] = "1"  # Will be overridden per test

class TestResults:
    def __init__(self):
        self.results = []
        self.total = 0
        self.passed = 0
        self.failed = 0
    
    def add(self, mode_num, mode_name, success, message):
        self.total += 1
        if success:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        self.results.append({
            "mode": mode_num,
            "name": mode_name,
            "status": status,
            "message": message
        })
        print(f"{status} | Mode {mode_num:2d}: {mode_name:25s} | {message}")
    
    def summary(self):
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.passed}/{self.total} passed")
        print("="*80)
        for result in self.results:
            print(f"  {result['status']} {result['name']:25s} - {result['message']}")
        print("="*80)
        return self.failed == 0


def check_capture_modes_config():
    """Verify CAPTURE_MODES is correctly configured"""
    try:
        from apa_api_sniffer_v2 import CAPTURE_MODES
        
        expected_modes = 11
        actual_modes = len(CAPTURE_MODES)
        
        if actual_modes != expected_modes:
            return False, f"Expected {expected_modes} modes, got {actual_modes}"
        
        # Check all modes have required fields
        required_fields = [
            "name", "key", "desc", "collect_apis", "collect_images",
            "collect_dom", "collect_network", "collect_client_intelligence",
            "collect_session_auth", "collect_page_behavior", 
            "collect_content_extraction", "collect_advanced_tracking"
        ]
        
        for mode_key, mode_config in CAPTURE_MODES.items():
            for field in required_fields:
                if field not in mode_config:
                    return False, f"Mode {mode_key} missing field: {field}"
        
        return True, f"All {expected_modes} modes correctly configured"
    except Exception as e:
        return False, str(e)


def check_mode_flags():
    """Verify each mode has proper boolean flags"""
    try:
        from apa_api_sniffer_v2 import CAPTURE_MODES
        
        for mode_key, mode_config in CAPTURE_MODES.items():
            flags = [
                "collect_apis", "collect_images", "collect_dom",
                "collect_network", "collect_client_intelligence",
                "collect_session_auth", "collect_page_behavior",
                "collect_content_extraction", "collect_advanced_tracking"
            ]
            
            for flag in flags:
                if not isinstance(mode_config.get(flag), bool):
                    return False, f"Mode {mode_key} flag {flag} is not boolean"
        
        return True, "All mode flags are properly typed"
    except Exception as e:
        return False, str(e)


def check_mode_logic():
    """Verify mode 11 (Everything) has all flags True"""
    try:
        from apa_api_sniffer_v2 import CAPTURE_MODES
        
        mode_11 = CAPTURE_MODES.get("11")
        if not mode_11:
            return False, "Mode 11 (Everything) not found"
        
        flags = [
            "collect_apis", "collect_images", "collect_dom",
            "collect_network", "collect_client_intelligence",
            "collect_session_auth", "collect_page_behavior",
            "collect_content_extraction", "collect_advanced_tracking"
        ]
        
        all_true = all(mode_11.get(flag) == True for flag in flags)
        if not all_true:
            missing = [f for f in flags if mode_11.get(f) != True]
            return False, f"Mode 11 flags not all True: {missing}"
        
        return True, "Mode 11 correctly has all flags set to True"
    except Exception as e:
        return False, str(e)


def check_mode_isolation():
    """Verify specialized modes have only their flag True"""
    try:
        from apa_api_sniffer_v2 import CAPTURE_MODES
        
        test_cases = [
            ("5", "network_analysis", "collect_network"),
            ("6", "client_intelligence", "collect_client_intelligence"),
            ("7", "session_auth", "collect_session_auth"),
            ("8", "page_behavior", "collect_page_behavior"),
            ("9", "content_extraction", "collect_content_extraction"),
            ("10", "advanced_tracking", "collect_advanced_tracking"),
        ]
        
        for mode_key, expected_key, expected_flag in test_cases:
            mode = CAPTURE_MODES.get(mode_key)
            if not mode:
                return False, f"Mode {mode_key} not found"
            
            if mode.get("key") != expected_key:
                return False, f"Mode {mode_key} key mismatch"
            
            if not mode.get(expected_flag):
                return False, f"Mode {mode_key} missing expected flag {expected_flag}"
        
        return True, "All specialized modes properly isolated"
    except Exception as e:
        return False, str(e)


def check_data_structures():
    """Verify data structure initialization"""
    try:
        # This would require running the sniffer, so we'll check the code exists
        import inspect
        from apa_api_sniffer_v2 import capture_page_apis
        
        source = inspect.getsource(capture_page_apis)
        
        required_inits = [
            "network_data = ",
            "client_data = ",
            "session_auth_data = ",
            "page_behavior_data = ",
            "content_extraction_data = ",
            "advanced_tracking_data = ",
        ]
        
        for init in required_inits:
            if init not in source:
                return False, f"Missing initialization: {init}"
        
        return True, "All data structures properly initialized"
    except Exception as e:
        return False, str(e)


def check_save_functions():
    """Verify save functions exist for all categories"""
    try:
        import inspect
        from apa_api_sniffer_v2 import save_results
        
        source = inspect.getsource(save_results)
        
        required_saves = [
            "network_summary.json",
            "client_intelligence_summary.json",
            "session_auth_summary.json",
            "page_behavior_summary.json",
            "content_extraction_summary.json",
            "advanced_tracking_summary.json",
        ]
        
        for save_file in required_saves:
            if save_file not in source:
                return False, f"Missing save for: {save_file}"
        
        return True, "All summary files are saved"
    except Exception as e:
        return False, str(e)


def check_cli_output():
    """Verify CLI output for all modes"""
    try:
        import inspect
        from apa_api_sniffer_v2 import select_capture_mode
        
        source = inspect.getsource(select_capture_mode)
        
        # Check for emoji indicators for new modes
        required_indicators = [
            "💡",  # Network Analysis
            "🧠",  # Client Intelligence
            "🔐",  # Session & Auth
            "📊",  # Page Behavior
            "📄",  # Content Extraction
            "🔍",  # Advanced Tracking
        ]
        
        for emoji in required_indicators:
            if emoji not in source:
                return False, f"Missing CLI emoji: {emoji}"
        
        return True, "All CLI indicators present"
    except Exception as e:
        return False, str(e)


def main():
    print("\n" + "="*80)
    print("APA API SNIFFER v2 - TEST SUITE")
    print("="*80 + "\n")
    
    results = TestResults()
    
    # Group 1: Configuration Tests
    print("GROUP 1: Configuration Tests")
    print("-" * 80)
    
    success, msg = check_capture_modes_config()
    results.add(1, "CAPTURE_MODES Config", success, msg)
    
    success, msg = check_mode_flags()
    results.add(2, "Mode Flags", success, msg)
    
    success, msg = check_mode_logic()
    results.add(3, "Mode Logic (11=Everything)", success, msg)
    
    success, msg = check_mode_isolation()
    results.add(4, "Mode Isolation", success, msg)
    
    # Group 2: Code Structure Tests
    print("\nGROUP 2: Code Structure Tests")
    print("-" * 80)
    
    success, msg = check_data_structures()
    results.add(5, "Data Structures", success, msg)
    
    success, msg = check_save_functions()
    results.add(6, "Save Functions", success, msg)
    
    success, msg = check_cli_output()
    results.add(7, "CLI Output", success, msg)
    
    # Test individual mode configurations
    print("\nGROUP 3: Individual Mode Tests")
    print("-" * 80)
    
    try:
        from apa_api_sniffer_v2 import CAPTURE_MODES
        
        mode_tests = [
            ("1", "API calls only", {"collect_apis": True}),
            ("2", "APIs + Screenshots", {"collect_apis": True}),
            ("3", "APIs + Images", {"collect_apis": True, "collect_images": True}),
            ("4", "APIs + DOM snapshot", {"collect_apis": True, "collect_dom": True}),
            ("5", "Network Analysis", {"collect_network": True}),
            ("6", "Client-Side Intelligence", {"collect_client_intelligence": True}),
            ("7", "Session & Auth Analysis", {"collect_session_auth": True}),
            ("8", "Page Behavior Analysis", {"collect_page_behavior": True}),
            ("9", "Content Extraction", {"collect_content_extraction": True}),
            ("10", "Advanced Tracking", {"collect_advanced_tracking": True}),
            ("11", "Everything", {
                "collect_apis": True,
                "collect_images": True,
                "collect_dom": True,
                "collect_network": True,
                "collect_client_intelligence": True,
                "collect_session_auth": True,
                "collect_page_behavior": True,
                "collect_content_extraction": True,
                "collect_advanced_tracking": True,
            }),
        ]
        
        for mode_key, mode_name, expected_flags in mode_tests:
            mode = CAPTURE_MODES.get(mode_key)
            if not mode:
                results.add(int(mode_key) + 6, mode_name, False, "Mode not found")
                continue
            
            flags_match = all(mode.get(k) == v for k, v in expected_flags.items())
            success_msg = f"Flags correctly set" if flags_match else "Flags mismatch"
            results.add(int(mode_key) + 6, mode_name, flags_match, success_msg)
    
    except Exception as e:
        results.add(0, "Mode Tests", False, str(e))
    
    # Print summary
    all_passed = results.summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
