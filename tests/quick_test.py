#!/usr/bin/env python3
"""
Quick Test Script for MotoSpect System
Tests basic connectivity to all services
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
TEST_VIN = "1HGBH41JXMN109186"
BACKEND_URL = "http://localhost:8000"

def test_backend_health():
    """Test if backend is running"""
    print("\n=== Testing Backend Health ===")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Backend is not accessible at", BACKEND_URL)
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_vin_decoder():
    """Test VIN decoder endpoint"""
    print("\n=== Testing VIN Decoder ===")
    print(f"Test VIN: {TEST_VIN}")
    try:
        response = requests.get(f"{BACKEND_URL}/api/vin/{TEST_VIN}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Vehicle: {data.get('make', 'Unknown')} {data.get('model', 'Unknown')} {data.get('year', 'Unknown')}")
            return True
        else:
            print(f"✗ VIN decoder failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_vehicle_database():
    """Test vehicle database endpoint"""
    print("\n=== Testing Vehicle Database ===")
    try:
        response = requests.get(f"{BACKEND_URL}/api/vehicle/database/{TEST_VIN}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✓ Vehicle database info retrieved")
            if 'recalls' in data:
                print(f"  - Recalls found: {len(data['recalls'])}")
            return True
        else:
            print(f"✗ Vehicle database failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_report_generation():
    """Test report generation endpoint"""
    print("\n=== Testing Report Generation ===")
    
    report_data = {
        "vin": TEST_VIN,
        "vehicle_info": {
            "make": "Honda",
            "model": "Accord",
            "year": 2021,
            "mileage": 45000
        },
        "parameters": {
            "rpm": 2500,
            "coolant_temp": 92,
            "oil_pressure": 45,
            "fuel_pressure": 380
        },
        "fault_codes": ["P0301", "P0171"],
        "scan_type": "comprehensive"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/report/generate",
            json=report_data,
            timeout=10
        )
        if response.status_code == 200:
            report = response.json()
            print("✓ Report generated successfully")
            if 'health_scores' in report:
                overall = report['health_scores'].get('overall', 0)
                print(f"  - Overall health: {overall}%")
            if 'recommendations' in report:
                print(f"  - Recommendations: {len(report['recommendations'])}")
            return True
        else:
            print(f"✗ Report generation failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_maintenance_schedule():
    """Test maintenance schedule endpoint"""
    print("\n=== Testing Maintenance Schedule ===")
    
    params = {
        "make": "Honda",
        "model": "Accord",
        "year": 2021,
        "mileage": 45000
    }
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/vehicle/maintenance",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            maintenance = response.json()
            print(f"✓ Maintenance schedule retrieved: {len(maintenance)} items")
            for item in maintenance[:3]:
                print(f"  - {item.get('service', 'Unknown')}: {item.get('interval_miles', 0)} miles")
            return True
        else:
            print(f"✗ Maintenance schedule failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("   MOTOSPECT QUICK SYSTEM TEST")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test VIN: {TEST_VIN}")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Backend Health", test_backend_health()))
    
    if results[0][1]:  # Only continue if backend is running
        results.append(("VIN Decoder", test_vin_decoder()))
        results.append(("Vehicle Database", test_vehicle_database()))
        results.append(("Report Generation", test_report_generation()))
        results.append(("Maintenance Schedule", test_maintenance_schedule()))
    
    # Summary
    print("\n" + "="*60)
    print("   TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} tests failed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
