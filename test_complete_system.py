#!/usr/bin/env python3
"""
Complete System Test for MOTOSPECT
Tests all major components and integration points
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = "http://localhost:8030"
FRONTEND_URL = "http://localhost:3030"
CUSTOMER_PORTAL_URL = "http://localhost:3040"

# Test VINs
TEST_VINS = {
    "honda": "1HGBH41JXMN109186",
    "bmw": "5UXWX7C5XEY000000",
    "audi": "WAUAFAFL1DN000000"
}

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")

def test_backend_health():
    """Test backend health endpoint"""
    print_header("Testing Backend Health")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is healthy - Status: {data['status']}")
            print_info(f"Services: {json.dumps(data['services'], indent=2)}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend - is it running?")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_vin_operations():
    """Test VIN validation, decoding, and recalls"""
    print_header("Testing VIN Operations")
    results = []
    
    for make, vin in TEST_VINS.items():
        print(f"\n{YELLOW}Testing {make.upper()} VIN: {vin}{RESET}")
        
        # Test validation
        try:
            response = requests.get(f"{BACKEND_URL}/api/vin/validate/{vin}")
            if response.status_code == 200:
                data = response.json()
                if data['valid']:
                    print_success(f"VIN validation passed")
                else:
                    print_error(f"VIN validation failed: {data['message']}")
                results.append(data['valid'])
            else:
                print_error(f"Validation endpoint returned {response.status_code}")
                results.append(False)
        except Exception as e:
            print_error(f"Validation error: {e}")
            results.append(False)
        
        # Test decoding
        try:
            response = requests.get(f"{BACKEND_URL}/api/vin/decode/{vin}")
            if response.status_code == 200:
                data = response.json()
                print_success(f"VIN decoded successfully")
                print_info(f"  Make: {data.get('make', 'N/A')}")
                print_info(f"  Model: {data.get('model', 'N/A')}")
                print_info(f"  Year: {data.get('year', 'N/A')}")
                results.append(True)
            else:
                print_error(f"Decode endpoint returned {response.status_code}")
                results.append(False)
        except Exception as e:
            print_error(f"Decode error: {e}")
            results.append(False)
        
        # Test recalls
        try:
            response = requests.get(f"{BACKEND_URL}/api/vin/recalls/{vin}")
            if response.status_code == 200:
                data = response.json()
                print_success(f"Recall check completed")
                print_info(f"  Recalls found: {data.get('recall_count', 0)}")
                results.append(True)
            else:
                print_error(f"Recalls endpoint returned {response.status_code}")
                results.append(False)
        except Exception as e:
            print_error(f"Recalls error: {e}")
            results.append(False)
    
    return all(results)

def test_cors_configuration():
    """Test CORS headers for different origins"""
    print_header("Testing CORS Configuration")
    
    origins = [
        ("Frontend", FRONTEND_URL),
        ("Customer Portal", CUSTOMER_PORTAL_URL),
        ("Localhost", "http://localhost:3000")
    ]
    
    results = []
    for name, origin in origins:
        try:
            # Test preflight
            response = requests.options(
                f"{BACKEND_URL}/api/vin/validate/TEST",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            if response.status_code in [200, 204]:
                cors_headers = response.headers.get('access-control-allow-origin')
                if cors_headers:
                    print_success(f"{name} CORS preflight passed")
                    results.append(True)
                else:
                    print_error(f"{name} CORS headers missing")
                    results.append(False)
            else:
                print_error(f"{name} preflight returned {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_error(f"{name} CORS test error: {e}")
            results.append(False)
    
    return all(results)

def test_diagnostic_scan():
    """Test diagnostic scan operations"""
    print_header("Testing Diagnostic Scan")
    
    try:
        # Start scan
        response = requests.post(
            f"{BACKEND_URL}/api/scan/start",
            json={
                "vin": TEST_VINS["honda"],
                "scan_type": "full",
                "options": {
                    "include_obd": True,
                    "include_thermal": True,
                    "include_visual": True
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            scan_id = data.get('scan_id')
            print_success(f"Scan started - ID: {scan_id}")
            
            # Check status
            time.sleep(1)
            status_response = requests.get(f"{BACKEND_URL}/api/scan/{scan_id}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                print_success(f"Scan status: {status.get('status', 'unknown')}")
                return True
            else:
                print_error(f"Status check failed: {status_response.status_code}")
                return False
        else:
            print_error(f"Scan start failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Scan test error: {e}")
        return False

def test_report_generation():
    """Test report generation"""
    print_header("Testing Report Generation")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/report/generate",
            json={
                "vin": TEST_VINS["honda"],
                "scan_data": {
                    "obd": {"fault_codes": []},
                    "thermal": {"max_temp": 85.5},
                    "visual": {"damage_detected": False}
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            report_id = data.get('report_id')
            print_success(f"Report generated - ID: {report_id}")
            return True
        else:
            print_error(f"Report generation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Report test error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"{BLUE}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║         MOTOSPECT COMPLETE SYSTEM TEST v2.0           ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    print_info(f"Test started at: {datetime.now().isoformat()}")
    print_info(f"Backend URL: {BACKEND_URL}")
    
    # Run tests
    test_results = {
        "Backend Health": test_backend_health(),
        "VIN Operations": test_vin_operations(),
        "CORS Configuration": test_cors_configuration(),
        "Diagnostic Scan": test_diagnostic_scan(),
        "Report Generation": test_report_generation()
    }
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}✓ ALL TESTS PASSED ({passed}/{total}){RESET}")
    else:
        print(f"{RED}✗ SOME TESTS FAILED ({passed}/{total} passed){RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
