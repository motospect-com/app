#!/usr/bin/env python3
"""Test Backend API and CORS Configuration"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from environment
backend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8030')
backend_port = os.getenv('BACKEND_PORT', '8030')
backend_url = f"http://localhost:{backend_port}"

print("=" * 60)
print("MOTOSPECT Backend API and CORS Test")
print("=" * 60)
print(f"Backend URL: {backend_url}")
print("-" * 60)

def test_endpoint(method, endpoint, headers=None, data=None, description=""):
    """Test a single API endpoint"""
    url = f"{backend_url}{endpoint}"
    print(f"\n{description}")
    print(f"Testing: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            response = requests.request(method, url, json=data, headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('access-control-allow-origin', 'Not set'),
            'Access-Control-Allow-Credentials': response.headers.get('access-control-allow-credentials', 'Not set'),
            'Access-Control-Allow-Methods': response.headers.get('access-control-allow-methods', 'Not set'),
        }
        print("CORS Headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
        
        # Show response content (first 200 chars)
        if response.text:
            content = response.text[:200]
            if len(response.text) > 200:
                content += "..."
            print(f"Response: {content}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Backend not running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Test cases
tests = []

# 1. Test root endpoint
tests.append(test_endpoint(
    "GET", "/",
    description="1. Root endpoint"
))

# 2. Test health check
tests.append(test_endpoint(
    "GET", "/health",
    description="2. Health check endpoint"
))

# 3. Test VIN decode endpoint
test_vin = "1HGBH41JXMN109186"
tests.append(test_endpoint(
    "GET", f"/api/vin/decode/{test_vin}",
    description="3. VIN decode endpoint"
))

# 4. Test VIN validation
tests.append(test_endpoint(
    "GET", f"/api/vin/validate/{test_vin}",
    description="4. VIN validation endpoint"
))

# 5. Test scan start endpoint
scan_data = {
    "vehicle_id": test_vin,
    "scan_type": "full",
    "options": {
        "include_obd": True,
        "include_thermal": True,
        "include_visual": True
    }
}
tests.append(test_endpoint(
    "POST", "/api/scan/start",
    data=scan_data,
    description="5. Start scan endpoint"
))

# 6. Test CORS preflight request
print("\n6. CORS Preflight Request Test")
print(f"Testing: OPTIONS {backend_url}/api/vin/decode/{test_vin}")
try:
    response = requests.options(
        f"{backend_url}/api/vin/decode/{test_vin}",
        headers={
            'Origin': 'http://localhost:3030',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        },
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print("CORS Headers:")
    print(f"  Allow-Origin: {response.headers.get('access-control-allow-origin', 'Not set')}")
    print(f"  Allow-Methods: {response.headers.get('access-control-allow-methods', 'Not set')}")
    print(f"  Allow-Headers: {response.headers.get('access-control-allow-headers', 'Not set')}")
    print(f"  Max-Age: {response.headers.get('access-control-max-age', 'Not set')}")
    tests.append(response.status_code in [200, 204])
except Exception as e:
    print(f"❌ CORS preflight failed: {e}")
    tests.append(False)

# 7. Test from different origins
print("\n7. Testing different origins")
origins = [
    "http://localhost:3030",  # Frontend
    "http://localhost:3040",  # Customer Portal
    "http://frontend:3030",   # Docker frontend
]

for origin in origins:
    print(f"\n  Origin: {origin}")
    try:
        response = requests.get(
            f"{backend_url}/api/vin/validate/{test_vin}",
            headers={'Origin': origin},
            timeout=5
        )
        allowed_origin = response.headers.get('access-control-allow-origin', 'None')
        if allowed_origin == origin or allowed_origin == '*':
            print(f"    ✓ Allowed (returned: {allowed_origin})")
        else:
            print(f"    ✗ Not allowed (returned: {allowed_origin})")
    except:
        print(f"    ✗ Request failed")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("-" * 60)
passed = sum(1 for t in tests if t)
total = len(tests)
print(f"Tests Passed: {passed}/{total}")

if passed == total:
    print("✓ All tests passed!")
else:
    print(f"✗ {total - passed} tests failed")

print("=" * 60)
