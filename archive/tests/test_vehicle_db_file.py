#!/usr/bin/env python3
"""Direct test of vehicle database functionality with file output"""

import asyncio
import sys
import traceback
sys.path.insert(0, '.')

from vehicle_database import VehicleDatabase

async def test_vehicle_database():
    """Test vehicle database functions directly"""
    
    # Open output file
    with open('vehicle_db_test_results.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("VEHICLE DATABASE INTEGRATION TEST\n")
        f.write("=" * 60 + "\n")
        
        try:
            # Initialize the database
            db = VehicleDatabase()
            f.write("✓ VehicleDatabase initialized\n")
            
            # Test VIN: 2020 Honda Civic (corrected valid check digit)
            test_vin = "19XFC2F52LE000576"
            
            # Test 1: Get comprehensive vehicle info
            f.write(f"\n1. Testing comprehensive vehicle info for VIN: {test_vin}\n")
            f.write("-" * 40 + "\n")
            try:
                vehicle_info = await db.get_vehicle_info(test_vin)
                f.write(f"✓ Make: {vehicle_info.specs.make}\n")
                f.write(f"✓ Model: {vehicle_info.specs.model}\n")
                f.write(f"✓ Year: {vehicle_info.specs.year}\n")
                f.write(f"✓ Engine: {vehicle_info.specs.engine_type}\n")
                f.write(f"✓ Recalls found: {len(vehicle_info.recalls)}\n")
                if vehicle_info.safety_rating:
                    f.write(f"✓ Safety rating: {vehicle_info.safety_rating.overall_rating}/5\n")
                f.write("SUCCESS: Vehicle info retrieved\n")
            except Exception as e:
                f.write(f"✗ ERROR: {e}\n")
                traceback.print_exc(file=f)
            
            # Test 2: Get maintenance schedule
            f.write(f"\n2. Testing maintenance schedule\n")
            f.write("-" * 40 + "\n")
            try:
                maintenance = await db.get_maintenance_schedule("Honda", "Civic", 2020, 30000)
                f.write(f"✓ Maintenance items: {len(maintenance)}\n")
                for item in maintenance[:3]:  # Show first 3 items
                    f.write(f"  - {item.service}: {item.description}\n")
                f.write("SUCCESS: Maintenance schedule retrieved\n")
            except Exception as e:
                f.write(f"✗ ERROR: {e}\n")
                traceback.print_exc(file=f)
            
            # Test 3: Get common problems
            f.write(f"\n3. Testing common problems retrieval\n")
            f.write("-" * 40 + "\n")
            try:
                problems = await db.get_common_problems("Honda", "Civic", 2020, 30000)
                f.write(f"✓ Common problems found: {len(problems)}\n")
                for problem in problems[:3]:  # Show first 3 problems
                    f.write(f"  - {problem.description} (Severity: {problem.severity})\n")
                f.write("SUCCESS: Common problems retrieved\n")
            except Exception as e:
                f.write(f"✗ ERROR: {e}\n")
                traceback.print_exc(file=f)
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("VEHICLE DATABASE TEST COMPLETE\n")
            f.write("=" * 60 + "\n")
            
        except Exception as e:
            f.write(f"\nFATAL ERROR: {e}\n")
            traceback.print_exc(file=f)
        
        f.flush()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_vehicle_database())
    print("Test results written to vehicle_db_test_results.txt")
