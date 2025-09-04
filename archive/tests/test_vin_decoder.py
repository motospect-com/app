#!/usr/bin/env python3
"""Test script for VIN decoder with NHTSA API integration"""

import asyncio
import logging
import sys
from vin_decoder import VINDecoder

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_vin_decoder():
    """Test the VIN decoder with both API and fallback modes"""
    
    # Test VINs
    test_vins = [
        '1HGBH41JXMN109186',  # Honda Civic
        '1G1YY22G965105430',  # Chevrolet Corvette
        'WBA3B3C50EF981467',  # BMW 3 Series
        'INVALID_VIN_TEST',   # Invalid VIN for testing
    ]
    
    # Test with NHTSA API
    print("=" * 60)
    print("Testing VIN Decoder with NHTSA API")
    print("=" * 60)
    
    decoder = VINDecoder(use_nhtsa_api=True)
    
    for vin in test_vins:
        print(f"\nTesting VIN: {vin}")
        print("-" * 40)
        
        # Validate
        is_valid = decoder.validate(vin)
        print(f"Valid: {is_valid}")
        
        if is_valid:
            # Decode
            try:
                result = decoder.decode(vin)
                if result:
                    print("Decode Result:")
                    for key, value in result.items():
                        if value:  # Only print non-empty values
                            print(f"  {key}: {value}")
                else:
                    print("  No decode result returned")
            except Exception as e:
                print(f"  Decode error: {e}")
            
            # Get recall info
            try:
                recalls = decoder.get_recall_info(vin)
                if recalls:
                    print(f"Recalls: {len(recalls)} found")
                    for i, recall in enumerate(recalls[:2], 1):  # Show first 2 recalls
                        print(f"  Recall {i}:")
                        for key, value in recall.items():
                            if value:
                                print(f"    {key}: {value}")
                else:
                    print("  No recalls found")
            except Exception as e:
                print(f"  Recall check error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing VIN Decoder with Fallback Mode")
    print("=" * 60)
    
    # Test fallback mode
    decoder_fallback = VINDecoder(use_nhtsa_api=False)
    
    test_vin = '1HGBH41JXMN109186'
    print(f"\nTesting VIN (fallback): {test_vin}")
    
    if decoder_fallback.validate(test_vin):
        result = decoder_fallback.decode(test_vin)
        if result:
            print("Fallback Decode Result:")
            for key, value in result.items():
                if value:
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_vin_decoder())
