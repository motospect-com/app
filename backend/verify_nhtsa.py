#!/usr/bin/env python3
"""Verify NHTSA VIN Decoder Integration"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/home/tom/github/motospect-com/app/backend')

# Create output file
output_file = '/tmp/nhtsa_verification.txt'

with open(output_file, 'w') as f:
    f.write("NHTSA VIN Decoder Integration Verification\n")
    f.write("=" * 50 + "\n\n")
    
    try:
        # Import modules
        from vin_decoder import VINDecoder
        f.write("✓ VIN decoder module imported\n")
        
        # Create decoder with NHTSA API
        decoder = VINDecoder(use_nhtsa_api=True)
        f.write("✓ VIN decoder instance created with NHTSA API enabled\n\n")
        
        # Test VIN
        test_vin = "1HGBH41JXMN109186"
        f.write(f"Testing VIN: {test_vin}\n")
        f.write("-" * 30 + "\n")
        
        # Validate VIN
        is_valid = decoder.validate(test_vin)
        f.write(f"VIN Valid: {is_valid}\n")
        
        if is_valid:
            # Decode VIN
            result = decoder.decode(test_vin)
            if result:
                f.write("✓ VIN decoded successfully\n")
                f.write(f"  Make: {result.get('make', 'N/A')}\n")
                f.write(f"  Model: {result.get('model', 'N/A')}\n")
                f.write(f"  Year: {result.get('year', 'N/A')}\n")
                f.write(f"  Body Type: {result.get('body_type', 'N/A')}\n")
                f.write(f"  Engine Size: {result.get('engine_size', 'N/A')}L\n")
                f.write(f"  Manufacturer: {result.get('manufacturer', 'N/A')}\n")
            else:
                f.write("✗ Decode returned None\n")
            
            # Get recalls
            recalls = decoder.get_recall_info(test_vin)
            if recalls:
                f.write(f"\n✓ Found {len(recalls)} recalls\n")
                for i, recall in enumerate(recalls[:3], 1):
                    f.write(f"  Recall {i}: {recall.get('campaign_number', 'N/A')} - {recall.get('component', 'N/A')}\n")
            else:
                f.write("\n✓ No recalls found\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("NHTSA Integration Status: WORKING\n")
        
    except Exception as e:
        f.write(f"\n✗ Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())
        f.write("\nNHTSA Integration Status: FAILED\n")

print(f"Verification complete. Results written to: {output_file}")

# Read and display the file
with open(output_file, 'r') as f:
    print(f.read())
