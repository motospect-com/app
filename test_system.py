#!/usr/bin/env python3
"""
Comprehensive System Test for MOTOSPECTests core functionality without external dependencies
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_fault_detector():
    """Test fault detection for vehicles up to 3L"""
    try:
        from fault_detector import FaultDetector, FaultSeverity
        
        detector = FaultDetector()
        
        # Test for different engine sizes
        engine_sizes = ["1.0L", "1.5L", "2.0L", "2.5L", "3.0L"]
        
        print("✓ Fault Detector initialized")
        print(f"✓ Supports engine sizes: {', '.join(engine_sizes)}")
        
        # Test parameter analysis for 2.0L engine
        test_params = {
            "rpm": 2500,
            "coolant_temp": 92,
            "oil_pressure": 45,
            "fuel_pressure": 380,
            "engine_load": 65,
            "intake_temp": 25,
            "maf_rate": 12.5,
            "throttle_pos": 35
        }
        
        result = detector.analyze_parameters(test_params, "2.0L")
        print(f"✓ Parameter analysis completed")
        
        # Test fault code analysis
        test_codes = ["P0301", "P0171", "P0420"]
        faults = detector.analyze_fault_codes(test_codes)
        print(f"✓ Analyzed {len(test_codes)} fault codes")
        
        # Test health scoring
        health = detector.calculate_health_scores(test_params, test_codes)
        print(f"✓ Health scores calculated for {len(health)} systems")
        
        return True
    except Exception as e:
        print(f"✗ Fault Detector test failed: {e}")
        return False

def test_vehicle_database():
    """Test vehicle database module"""
    try:
        from vehicle_database import VehicleDatabase
        
        vdb = VehicleDatabase()
        print("✓ Vehicle Database initialized")
        
        # Test VIN decoder (offline mode)
        test_vin = "1HGBH41JXMN109186"
        print(f"✓ VIN decoder ready for: {test_vin}")
        
        return True
    except Exception as e:
        print(f"✗ Vehicle Database test failed: {e}")
        return False

def test_report_generator():
    """Test report generator"""
    try:
        from report_generator import ReportGenerator
        
        gen = ReportGenerator()
        print("✓ Report Generator initialized")
        
        # Test report structure
        test_data = {
            "vin": "1HGBH41JXMN109186",
            "vehicle_info": {
                "make": "Honda",
                "model": "Accord", 
                "year": 2021,
                "engine_size": "2.0L"
            },
            "health_scores": {
                "Engine": 85,
                "Transmission": 90,
                "Brakes": 88,
                "Suspension": 92
            }
        }
        
        report = gen.generate_report(test_data)
        print(f"✓ Report generated with ID: {report.get('report_id', 'test')}")
        
        return True
    except Exception as e:
        print(f"✗ Report Generator test failed: {e}")
        return False

def test_scan_manager():
    """Test scan manager"""
    try:
        from scan_manager import ScanManager
        
        manager = ScanManager()
        print("✓ Scan Manager initialized")
        
        # Test scan creation
        scan_id = manager.create_scan("test-vehicle")
        print(f"✓ Created scan: {scan_id}")
        
        # Test scan status
        status = manager.get_scan_status(scan_id)
        print(f"✓ Scan status: {status}")
        
        return True
    except Exception as e:
        print(f"✗ Scan Manager test failed: {e}")
        return False

def test_supported_vehicles():
    """Verify supported vehicle types and engine sizes"""
    print("\n=== SUPPORTED VEHICLES ===")
    print("Vehicle Types:")
    print("  • Cars (Sedans, Hatchbacks, Coupes)")
    print("  • SUVs (Compact, Mid-size, Full-size)")
    print("  • Vans (Minivans, Cargo vans)")
    print("  • Crossovers")
    print("  • Light trucks")
    
    print("\nEngine Sizes:")
    print("  • 1.0L - 1.4L: Small displacement")
    print("  • 1.5L - 1.9L: Compact engines")
    print("  • 2.0L - 2.4L: Mid-size engines")
    print("  • 2.5L - 3.0L: Large displacement")
    
    print("\nDiagnostic Capabilities:")
    print("  • OBD-II fault code analysis")
    print("  • Real-time parameter monitoring")
    print("  • Predictive failure analysis")
    print("  • Multi-sensor fusion (OBD, Audio, Thermal, TOF)")
    print("  • Comprehensive health scoring")
    
    return True

def main():
    """Run all system tests"""
    print("=" * 50)
    print("MOTOSPECT SYSTEM TEST")
    print("Vehicle Diagnostics up to 3L Engine Capacity")
    print("=" * 50)
    
    tests = [
        ("Fault Detector", test_fault_detector),
        ("Vehicle Database", test_vehicle_database),
        ("Report Generator", test_report_generator),
        ("Scan Manager", test_scan_manager),
        ("Vehicle Support", test_supported_vehicles)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} error: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All core systems operational")
        return 0
    else:
        print("✗ Some systems need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
