#!/usr/bin/env python3
"""Comprehensive test for NHTSA VIN Decoder API integration"""

import asyncio
import logging
import json
from vin_decoder import VINDecoder
from external_apis import NHTSAApi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_direct_api():
    """Test NHTSA API directly"""
    print("\n" + "="*60)
    print("Testing Direct NHTSA API Calls")
    print("="*60)
    
    api = NHTSAApi()
    test_vin = "1HGBH41JXMN109186"
    
    # Test VIN decoding
    print(f"\nDecoding VIN: {test_vin}")
    try:
        async with api:
            result = await api.decode_vin(test_vin)
            if result:
                print("✓ Decode successful:")
                # Show key fields
                important_fields = ['make', 'model', 'year', 'manufacturer', 
                                  'body_type', 'engine_cylinders', 'drive_type']
                for field in important_fields:
                    if field in result:
                        print(f"  {field}: {result[field]}")
            else:
                print("✗ Decode returned None")
    except Exception as e:
        print(f"✗ API Error: {e}")
    
    # Test recall information
    print(f"\nGetting recalls for VIN: {test_vin}")
    try:
        async with api:
            recalls = await api.get_recall_info(test_vin)
            if recalls:
                print(f"✓ Found {len(recalls)} recalls")
                for i, recall in enumerate(recalls[:2], 1):
                    print(f"  Recall {i}: {recall.get('Component', 'Unknown')}")
            else:
                print("✓ No recalls found")
    except Exception as e:
        print(f"✗ Recall API Error: {e}")

def test_sync_decoder():
    """Test synchronous VIN decoder wrapper"""
    print("\n" + "="*60)
    print("Testing Synchronous VIN Decoder")
    print("="*60)
    
    decoder = VINDecoder(use_nhtsa_api=True)
    test_vins = [
        "1HGBH41JXMN109186",  # Honda
        "1G1YY22G965105430",  # Chevrolet
        "WBA3B3C50EF981467",  # BMW
    ]
    
    for vin in test_vins:
        print(f"\nTesting VIN: {vin}")
        
        # Validate
        is_valid = decoder.validate(vin)
        print(f"  Valid: {is_valid}")
        
        if is_valid:
            # Decode
            result = decoder.decode(vin)
            if result:
                print("  ✓ Decoded:")
                print(f"    Make: {result.get('make', 'Unknown')}")
                print(f"    Model: {result.get('model', 'Unknown')}")
                print(f"    Year: {result.get('year', 'Unknown')}")
            else:
                print("  ✗ Decode failed")
            
            # Get recalls
            recalls = decoder.get_recall_info(vin)
            if recalls:
                print(f"  ✓ {len(recalls)} recalls found")
            else:
                print("  ✓ No recalls")

def test_fallback_mode():
    """Test fallback mode when API is disabled"""
    print("\n" + "="*60)
    print("Testing Fallback Mode (No API)")
    print("="*60)
    
    decoder = VINDecoder(use_nhtsa_api=False)
    test_vin = "1HGBH41JXMN109186"
    
    print(f"\nTesting VIN (fallback): {test_vin}")
    
    if decoder.validate(test_vin):
        result = decoder.decode(test_vin)
        if result:
            print("✓ Fallback decode successful:")
            print(f"  Make: {result.get('make', 'Unknown')}")
            print(f"  Model: {result.get('model', 'Unknown')}")
            print(f"  Year: {result.get('year', 'Unknown')}")
        else:
            print("✗ Fallback decode failed")

async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" NHTSA VIN DECODER API INTEGRATION TEST ")
    print("="*70)
    
    # Test direct API calls
    await test_direct_api()
    
    # Test synchronous wrapper
    test_sync_decoder()
    
    # Test fallback mode
    test_fallback_mode()
    
    print("\n" + "="*70)
    print(" TEST COMPLETE ")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
