#!/usr/bin/env python3
"""
Test script for Vehicle Database API integration
"""
import asyncio
import aiohttp
import json


async def test_backend_vehicle_apis():
    """Test vehicle database endpoints via backend API"""
    base_url = "http://localhost:8000"
    
    # Test VIN lookup
    print("=" * 60)
    print("Testing Vehicle Database API Integration")
    print("=" * 60)
    
    # Test with a sample VIN
    vin = "1HGCM82633A123456"
    print(f"\n1. Testing VIN lookup: {vin}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test vehicle database endpoint
            async with session.get(f"{base_url}/api/vehicle/database/{vin}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        print("✓ Vehicle database lookup successful")
                        vehicle_data = data.get("data", {})
                        
                        # Display NHTSA data
                        if vehicle_data.get("nhtsa"):
                            print("\nNHTSA Data:")
                            for key, value in vehicle_data["nhtsa"].items():
                                print(f"  {key}: {value}")
                        
                        # Display safety ratings
                        if vehicle_data.get("safety_ratings"):
                            print("\nSafety Ratings:")
                            for key, value in vehicle_data["safety_ratings"].items():
                                print(f"  {key}: {value}")
                        
                        # Display recalls
                        if vehicle_data.get("recalls"):
                            print(f"\nRecalls Found: {len(vehicle_data['recalls'])}")
                            for recall in vehicle_data["recalls"][:2]:  # Show first 2
                                print(f"  - {recall.get('component')}: {recall.get('summary')[:100]}...")
                    else:
                        print(f"✗ Error: {data.get('message')}")
                else:
                    print(f"✗ HTTP Error: {response.status}")
            
            # Test maintenance schedule
            print("\n2. Testing Maintenance Schedule")
            params = {
                "make": "Honda",
                "model": "Accord",
                "year": 2020,
                "mileage": 45000
            }
            
            async with session.get(f"{base_url}/api/vehicle/maintenance", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        print("✓ Maintenance schedule retrieved")
                        schedule = data.get("schedule", [])
                        print(f"  Services due: {len(schedule)}")
                        for service in schedule:
                            print(f"  - {service['service']}: ${service['estimated_cost']['min']}-${service['estimated_cost']['max']}")
                else:
                    print(f"✗ HTTP Error: {response.status}")
            
            # Test common problems
            print("\n3. Testing Common Problems")
            params = {
                "make": "Honda",
                "model": "Accord", 
                "year": 2010
            }
            
            async with session.get(f"{base_url}/api/vehicle/common-problems", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        print("✓ Common problems retrieved")
                        problems = data.get("problems", [])
                        print(f"  Known issues: {len(problems)}")
                        for problem in problems:
                            print(f"  - {problem['issue']}: ${problem['estimated_repair_cost']['min']}-${problem['estimated_repair_cost']['max']}")
                else:
                    print(f"✗ HTTP Error: {response.status}")
                    
    except aiohttp.ClientError as e:
        print(f"✗ Connection error: {e}")
        print("Make sure the backend is running on port 8000")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Vehicle Database API Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_backend_vehicle_apis())
