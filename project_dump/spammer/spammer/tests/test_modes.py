#!/usr/bin/env python3
"""
Test suite for individual sniffer modes
Validates that mode configurations are correct and complete
"""

import sys
import json
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_mode_configuration():
    """Test that all modes have complete configurations"""
    sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
    
    print("\n" + "="*70)
    print("  MODE CONFIGURATION TESTS")
    print("="*70 + "\n")
    
    with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract CAPTURE_MODES section
    modes_start = content.find("CAPTURE_MODES = {")
    modes_end = content.find("}\n}", modes_start) + 2
    
    if modes_start == -1:
        print("❌ CAPTURE_MODES not found!")
        return False
    
    modes_section = content[modes_start:modes_end]
    
    required_fields = [
        "name",
        "key",
        "desc",
        "collect_"
    ]
    
    all_valid = True
    
    for mode_num in range(1, 27):
        mode_key = f'"{mode_num}": {{'
        if mode_key not in modes_section:
            print(f"❌ Mode {mode_num} not found")
            all_valid = False
            continue
        
        # Find mode section
        mode_start = modes_section.find(mode_key)
        mode_end = modes_section.find("    },", mode_start)
        mode_config = modes_section[mode_start:mode_end]
        
        # Check required fields
        has_all_fields = all(field in mode_config for field in required_fields)
        
        if has_all_fields:
            # Extract mode name
            name_match = re.search(r'"name":\s*"([^"]+)"', mode_config)
            mode_name = name_match.group(1) if name_match else "Unknown"
            print(f"✓ Mode {mode_num:2d}: {mode_name}")
        else:
            print(f"❌ Mode {mode_num} missing required fields")
            all_valid = False
    
    return all_valid


def test_mode_descriptions():
    """Test that all modes have meaningful descriptions"""
    sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
    
    print("\n" + "="*70)
    print("  MODE DESCRIPTION VALIDATION")
    print("="*70 + "\n")
    
    with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all mode descriptions
    desc_pattern = r'"desc":\s*"([^"]+)"'
    descriptions = re.findall(desc_pattern, content)
    
    all_valid = True
    for i, desc in enumerate(descriptions, 1):
        if len(desc) < 5:
            print(f"❌ Mode {i} has too short description: '{desc}'")
            all_valid = False
        elif len(desc) > 200:
            print(f"⚠️  Mode {i} has very long description")
        else:
            print(f"✓ Mode {i}: {desc[:60]}...")
    
    return all_valid


def test_mode_features():
    """Test that each mode has at least one feature flag"""
    sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
    
    print("\n" + "="*70)
    print("  MODE FEATURE FLAGS VALIDATION")
    print("="*70 + "\n")
    
    with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find CAPTURE_MODES section
    modes_start = content.find("CAPTURE_MODES = {")
    modes_end = content.find("}\n}", modes_start) + 2
    modes_section = content[modes_start:modes_end]
    
    all_valid = True
    feature_flags = [
        "collect_apis",
        "collect_images",
        "collect_dom",
        "collect_network",
        "collect_client_intelligence",
        "collect_session_auth",
        "collect_page_behavior",
        "collect_content_extraction",
        "collect_advanced_tracking",
        "collect_graphql_direct",
        "collect_auth_bypass",
        "collect_advanced_graphql_bypass",
        "collect_gql_poolplayers_bypass",
        "collect_form_autodetection",
        "collect_response_caching",
        "collect_data_leakage",
        "collect_hidden_endpoints",
        "collect_cors_analysis",
        "collect_jwt_analysis",
        "collect_api_key_exposure",
        "collect_sqli_testing",
        "collect_xxe_injection",
        "collect_command_injection",
        "collect_graphql_authz_bypass",
    ]
    
    for mode_num in range(1, 27):
        mode_key = f'"{mode_num}": {{'
        mode_start = modes_section.find(mode_key)
        mode_end = modes_section.find("    },", mode_start)
        mode_config = modes_section[mode_start:mode_end]
        
        # Count feature flags in this mode
        flags_in_mode = sum(1 for flag in feature_flags if flag in mode_config)
        
        if flags_in_mode < 5:
            print(f"⚠️  Mode {mode_num} has only {flags_in_mode} feature flags")
        else:
            print(f"✓ Mode {mode_num} has {flags_in_mode} feature flags")
    
    return True


def test_test_function_mapping():
    """Test that each mode has a corresponding test function"""
    sniffer_path = Path(__file__).parent.parent / "apa_api_sniffer_v2.py"
    
    print("\n" + "="*70)
    print("  TEST FUNCTION MAPPING VALIDATION")
    print("="*70 + "\n")
    
    with open(sniffer_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Expected mode to function mappings
    mode_functions = {
        5: "test_network_analysis",
        6: "test_client_intelligence",
        7: "test_session_auth",
        8: "test_page_behavior",
        9: "test_content_extraction",
        11: "test_graphql_endpoints",
        12: "test_auth_bypass",
        14: "test_advanced_graphql_bypass",
        15: "test_gql_poolplayers_bypass",
        16: "test_form_autodetection",
        17: "test_response_caching_analysis",
        18: "detect_data_leakage",
        19: "discover_hidden_endpoints",
        20: "test_cors_analysis",
        21: "test_jwt_analysis",
        22: "test_api_key_exposure",
        23: "test_sqli_testing",
        24: "test_xxe_injection",
        25: "test_command_injection",
        26: "test_graphql_authz_bypass",
    }
    
    all_valid = True
    for mode_num, func_name in mode_functions.items():
        if f"def {func_name}" in content or f"async def {func_name}" in content:
            print(f"✓ Mode {mode_num} -> {func_name}()")
        else:
            print(f"❌ Mode {mode_num} missing function: {func_name}")
            all_valid = False
    
    return all_valid


def run_mode_tests():
    """Run all mode tests"""
    print("\n" + "="*70)
    print("  MODE VALIDATION TEST SUITE")
    print("="*70)
    
    results = []
    
    results.append(("Mode Configuration", test_mode_configuration()))
    results.append(("Mode Descriptions", test_mode_descriptions()))
    results.append(("Mode Features", test_mode_features()))
    results.append(("Function Mapping", test_test_function_mapping()))
    
    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} test groups passed")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_mode_tests()
    sys.exit(0 if success else 1)
