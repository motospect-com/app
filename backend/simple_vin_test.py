#!/usr/bin/env python3
"""Simple test to verify NHTSA VIN decoder integration"""

import sys
import json

def test_vin_decoder():
    """Simple test of VIN decoder functionality"""
    try:
        # Import the VIN decoder
        from vin_decoder import VINDecoder
        print("✓ VIN decoder imported successfully")
        
        # Create decoder with NHTSA API enabled
        decoder = VINDecoder(use_nhtsa_api=True)
        print("✓ VIN decoder instance created")
        
        # Test VINs
        test_vins = [
            "1HGBH41JXMN109186",  # Honda Civic
            "1G1YY22G965105430",  # Chevrolet Corvette
        ]
        
        for vin in test_vins:
            print(f"\n--- Testing VIN: {vin} ---")
            
            # Validate
            is_valid = decoder.validate(vin)
            print(f"Valid: {is_valid}")
            
            if is_valid:
                # Decode
                result = decoder.decode(vin)
                if result:
                    print("Decoded successfully:")
                    print(f"  Make: {result.get('make', 'N/A')}")
                    print(f"  Model: {result.get('model', 'N/A')}")
                    print(f"  Year: {result.get('year', 'N/A')}")
                    print(f"  Body Type: {result.get('body_type', 'N/A')}")
                    print(f"  Engine Size: {result.get('engine_size', 'N/A')}L")
                else:
                    print("Decode returned None")
                
                # Get recalls
                recalls = decoder.get_recall_info(vin)
                if recalls:
                    print(f"Recalls: {len(recalls)} found")
                else:
                    print("Recalls: None found")
        
        print("\n✓ Test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vin_decoder()
    sys.exit(0 if success else 1)
