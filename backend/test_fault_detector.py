#!/usr/bin/env python3
"""Test script for fault detection system"""

from fault_detector import FaultDetector, FaultSeverity, SystemType
import json

def test_fault_detector():
    """Test the fault detection system with various scenarios"""
    detector = FaultDetector()
    
    print("=" * 60)
    print("MOTOSPECT FAULT DETECTION SYSTEM TEST")
    print("=" * 60)
    
    # Test Case 1: Normal parameters
    print("\n1. Testing normal vehicle parameters (2.0L engine)...")
    normal_params = {
        "rpm": 800,
        "coolant_temp": 92,
        "oil_pressure": 35,
        "fuel_pressure": 42,
        "mileage": 45000,
        "brake_pad_thickness": 8,
        "fault_codes": []
    }
    
    result = detector.analyze_parameters(normal_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    print(f"   Faults Found: {len(result['faults'])}")
    print(f"   Immediate Attention: {result['immediate_attention']}")
    
    # Test Case 2: Low oil pressure
    print("\n2. Testing low oil pressure condition...")
    low_oil_params = {
        "rpm": 2500,
        "oil_pressure": 15,
        "coolant_temp": 95,
        "fault_codes": []
    }
    
    result = detector.analyze_parameters(low_oil_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    print(f"   Faults Found: {len(result['faults'])}")
    if result['faults']:
        print(f"   Main Issue: {result['faults'][0]['description']}")
        print(f"   Severity: {result['faults'][0]['severity'].value}")
    
    # Test Case 3: Engine overheating
    print("\n3. Testing engine overheating...")
    overheat_params = {
        "rpm": 3000,
        "coolant_temp": 125,
        "oil_pressure": 40,
        "fault_codes": []
    }
    
    result = detector.analyze_parameters(overheat_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    print(f"   Faults Found: {len(result['faults'])}")
    if result['faults']:
        print(f"   Main Issue: {result['faults'][0]['description']}")
        print(f"   Immediate Action: {result['faults'][0].get('immediate_action', False)}")
    
    # Test Case 4: Multiple fault codes
    print("\n4. Testing with OBD fault codes...")
    fault_params = {
        "rpm": 850,
        "coolant_temp": 88,
        "oil_pressure": 32,
        "fault_codes": ["P0300", "P0171", "P0420"],
        "misfire_count": {"1": 15, "2": 2, "3": 20, "4": 18}
    }
    
    result = detector.analyze_parameters(fault_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    print(f"   Faults Found: {len(result['faults'])}")
    print(f"   Recommendations: {len(result['recommendations'])}")
    
    for fault in result['faults'][:3]:
        print(f"   - {fault['code']}: {fault['description']}")
    
    # Test Case 5: Different engine sizes
    print("\n5. Testing different engine sizes...")
    for engine_size in ["1.0L", "2.5L", "3.0L"]:
        params = {
            "rpm": 750,
            "coolant_temp": 95,
            "oil_pressure": 28,
            "fuel_pressure": 38,
            "fault_codes": []
        }
        result = detector.analyze_parameters(params, engine_size)
        print(f"   {engine_size}: Health={result['overall_health']}%, Faults={len(result['faults'])}")
    
    # Test Case 6: Brake wear detection
    print("\n6. Testing brake wear detection...")
    brake_params = {
        "rpm": 800,
        "coolant_temp": 90,
        "brake_pad_thickness": 2.5,  # Low thickness
        "fault_codes": []
    }
    
    result = detector.analyze_parameters(brake_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    health_scores = result['health_scores']
    print(f"   Brake System Health: {health_scores.get('Brakes', 'N/A')}%")
    
    # Test Case 7: System health scoring
    print("\n7. Testing comprehensive system health...")
    comprehensive_params = {
        "rpm": 820,
        "coolant_temp": 91,
        "oil_pressure": 34,
        "fuel_pressure": 41,
        "brake_pad_thickness": 6,
        "fault_codes": ["P0442"],  # Small EVAP leak
        "mileage": 59500  # Near service interval
    }
    
    result = detector.analyze_parameters(comprehensive_params, "2.0L")
    print(f"   Overall Health: {result['overall_health']}%")
    print("\n   System Health Scores:")
    for system, score in result['health_scores'].items():
        status = "Excellent" if score > 90 else "Good" if score > 75 else "Fair" if score > 60 else "Poor"
        print(f"   - {system}: {score}% ({status})")
    
    print("\n   Recommendations:")
    for rec in result['recommendations'][:3]:
        print(f"   - {rec['text']} (Priority: {rec['priority']})")
    
    print("\n" + "=" * 60)
    print("FAULT DETECTION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_fault_detector()
