#!/usr/bin/env python3
"""Direct test of NHTSA API without dependencies"""

import json
import urllib.request
import urllib.parse

def test_nhtsa_api_directly():
    """Test NHTSA API directly using urllib"""
    test_vin = "1HGBH41JXMN109186"
    
    print(f"Testing NHTSA API with VIN: {test_vin}")
    print("-" * 50)
    
    # Test VIN decode API
    decode_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvaluesextended/{test_vin}?format=json"
    
    try:
        print("Calling NHTSA Decode API...")
        with urllib.request.urlopen(decode_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get('Results'):
            result = data['Results'][0]
            print("✓ Decode successful!")
            print(f"  Make: {result.get('Make', 'N/A')}")
            print(f"  Model: {result.get('Model', 'N/A')}")
            print(f"  Year: {result.get('ModelYear', 'N/A')}")
            print(f"  Body Class: {result.get('BodyClass', 'N/A')}")
            print(f"  Engine Cylinders: {result.get('EngineCylinders', 'N/A')}")
            print(f"  Drive Type: {result.get('DriveType', 'N/A')}")
            print(f"  Manufacturer: {result.get('Manufacturer', 'N/A')}")
        else:
            print("✗ No results returned")
            
    except Exception as e:
        print(f"✗ API Error: {e}")
    
    # Test recall API
    print("\nTesting NHTSA Recall API...")
    recall_url = f"https://api.nhtsa.gov/recalls/recallsByVin?vin={test_vin}"
    
    try:
        with urllib.request.urlopen(recall_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get('results'):
            recalls = data['results']
            print(f"✓ Found {len(recalls)} recalls")
            for i, recall in enumerate(recalls[:2], 1):
                print(f"  Recall {i}: {recall.get('Component', 'N/A')}")
        else:
            print("✓ No recalls found")
            
    except Exception as e:
        print(f"✗ Recall API Error: {e}")
    
    print("\nNHTSA API test complete!")

if __name__ == "__main__":
    test_nhtsa_api_directly()
