#!/usr/bin/env python3
"""Direct test of vehicle database functionality without backend dependencies"""

import asyncio
import sys
sys.path.insert(0, '.')

from vehicle_database import VehicleDatabase

async def test_vehicle_database():
    """Test vehicle database functions directly"""
    
    # Initialize the database
    db = VehicleDatabase()
    
    # Test VIN: 2020 Honda Civic
    # Corrected VIN with valid check digit (2020 Honda Civic)
    test_vin = "19XFC2F52LE000576"
    
    print("=" * 60)
    print("VEHICLE DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Get comprehensive vehicle info
    print(f"\n1. Testing comprehensive vehicle info for VIN: {test_vin}")
    print("-" * 40)
    try:
        vehicle_info = await db.get_vehicle_info(test_vin)
        print(f"✓ Make: {vehicle_info.specs.make}")
        print(f"✓ Model: {vehicle_info.specs.model}")
        print(f"✓ Year: {vehicle_info.specs.year}")
        print(f"✓ Engine: {vehicle_info.specs.engine_type}")
        print(f"✓ Recalls found: {len(vehicle_info.recalls)}")
        if vehicle_info.safety_rating:
            print(f"✓ Safety rating: {vehicle_info.safety_rating.overall_rating}/5")
        print("SUCCESS: Vehicle info retrieved")
    except Exception as e:
        print(f"✗ ERROR: {e}")
    
    # Test 2: Get maintenance schedule
    print(f"\n2. Testing maintenance schedule")
    print("-" * 40)
    try:
        maintenance = await db.get_maintenance_schedule("Honda", "Civic", 2020, 30000)
        print(f"✓ Maintenance items: {len(maintenance)}")
        for item in maintenance[:3]:  # Show first 3 items
            print(f"  - {item.service}: {item.description}")
        print("SUCCESS: Maintenance schedule retrieved")
    except Exception as e:
        print(f"✗ ERROR: {e}")
    
    # Test 3: Get common problems
    print(f"\n3. Testing common problems retrieval")
    print("-" * 40)
    try:
        problems = await db.get_common_problems("Honda", "Civic", 2020, 30000)
        print(f"✓ Common problems found: {len(problems)}")
        for problem in problems[:3]:  # Show first 3 problems
            print(f"  - {problem.description} (Severity: {problem.severity})")
        print("SUCCESS: Common problems retrieved")
    except Exception as e:
        print(f"✗ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("VEHICLE DATABASE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_vehicle_database())
