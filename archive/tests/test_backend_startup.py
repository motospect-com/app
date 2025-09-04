#!/usr/bin/env python3
import sys
import traceback

try:
    print("Starting backend test...")
    
    from fastapi import FastAPI
    print("✓ FastAPI imported")
    
    from mqtt_bridge import MQTTBridge
    print("✓ MQTTBridge imported")
    
    from vin_decoder import VINDecoder
    print("✓ VINDecoder imported")
    
    from obd_interface import OBDInterface
    print("✓ OBDInterface imported")
    
    from fault_detector import FaultDetector
    print("✓ FaultDetector imported")
    
    from vehicle_database import VehicleDatabase
    print("✓ VehicleDatabase imported")
    
    from scan_manager import ScanManager
    print("✓ ScanManager imported")
    
    from report_generator import ReportGenerator
    print("✓ ReportGenerator imported")
    
    print("\nInitializing services...")
    
    mqtt_bridge = MQTTBridge()
    print("✓ MQTTBridge initialized")
    
    vin_decoder = VINDecoder()
    print("✓ VINDecoder initialized")
    
    obd = OBDInterface()
    print("✓ OBDInterface initialized")
    
    fault_detector = FaultDetector()
    print("✓ FaultDetector initialized")
    
    vehicle_db = VehicleDatabase()
    print("✓ VehicleDatabase initialized")
    
    scan_mgr = ScanManager()
    print("✓ ScanManager initialized")
    
    report_gen = ReportGenerator()
    print("✓ ReportGenerator initialized")
    
    print("\nCreating FastAPI app...")
    app = FastAPI(title="MotoSpect Backend API", version="1.0.0")
    print("✓ FastAPI app created")
    
    print("\nAttempting to connect MQTT...")
    try:
        mqtt_bridge.connect()
        print("✓ MQTT connect attempted")
    except Exception as e:
        print(f"⚠ MQTT connect failed: {e}")
    
    print("\nAll components loaded successfully!")
    print("Backend should be ready to start.")
    
except Exception as e:
    print(f"\n✗ Error occurred: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
