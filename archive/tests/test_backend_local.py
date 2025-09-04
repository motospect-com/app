#!/usr/bin/env python3
"""Test backend locally without Docker"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = os.getenv('BACKEND_PATH', '/home/tom/github/motospect-com/app/backend')
sys.path.insert(0, backend_path)

print("Testing MOTOSPECT Backend Components")
print("=" * 60)

# Test imports
components = []

try:
    from vin_decoder import VINDecoder
    components.append("✓ VIN Decoder")
except Exception as e:
    components.append(f"✗ VIN Decoder: {e}")

try:
    from obd_interface import OBDInterface
    components.append("✓ OBD Interface")
except Exception as e:
    components.append(f"✗ OBD Interface: {e}")

try:
    from fault_detector import FaultDetector
    components.append("✓ Fault Detector")
except Exception as e:
    components.append(f"✗ Fault Detector: {e}")

try:
    from vehicle_database import VehicleDatabase
    components.append("✓ Vehicle Database")
except Exception as e:
    components.append(f"✗ Vehicle Database: {e}")

try:
    from motospect_core import MotospectCore
    components.append("✓ Motospect Core")
except Exception as e:
    components.append(f"✗ Motospect Core: {e}")

try:
    from sensor_modules import SensorManager
    components.append("✓ Sensor Manager")
except Exception as e:
    components.append(f"✗ Sensor Manager: {e}")

try:
    from external_apis import NHTSAApi
    components.append("✓ NHTSA API")
except Exception as e:
    components.append(f"✗ NHTSA API: {e}")

for component in components:
    print(component)

print("\n" + "-" * 60)
print("Testing VIN Decoder with NHTSA API")
print("-" * 60)

try:
    decoder = VINDecoder()
    test_vin = "1HGBH41JXMN109186"
    
    print(f"VIN: {test_vin}")
    print(f"Valid: {decoder.validate(test_vin)}")
    
    result = decoder.decode(test_vin)
    if result:
        print("Decode successful:")
        print(f"  Make: {result.get('make')}")
        print(f"  Model: {result.get('model')}")
        print(f"  Year: {result.get('year')}")
    else:
        print("Decode failed")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Backend components test complete")
