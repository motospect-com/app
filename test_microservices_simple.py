#!/usr/bin/env python3
"""
Simple microservices test without complex Service Manager
Direct testing of each microservice
"""
import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def test_service_startup(service_name, service_dir, port):
    """Test if a service can start and respond to health checks"""
    print(f"\n🔍 Testing {service_name}...")
    
    # Change to service directory
    service_path = Path(f"services/{service_dir}")
    if not service_path.exists():
        print(f"❌ Service directory not found: {service_path}")
        return False
    
    try:
        # Set environment
        env = os.environ.copy()
        env['PORT'] = str(port)
        env['PYTHONPATH'] = f"{Path.cwd()}/backend:{env.get('PYTHONPATH', '')}"
        
        # Try to start service
        print(f"   Starting on port {port}...")
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=service_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"   ❌ Process died. Stdout: {stdout.decode()[:200]}")
            print(f"   ❌ Stderr: {stderr.decode()[:200]}")
            return False
        
        # Try health check
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {service_name} healthy")
                success = True
            else:
                print(f"   ⚠️ {service_name} responded but not healthy: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Health check failed: {e}")
            success = False
        
        # Cleanup
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"   ❌ Error testing {service_name}: {e}")
        return False

def main():
    """Test all microservices"""
    print("🧪 MOTOSPECT Microservices Simple Test")
    print("=" * 50)
    
    services = [
        ("VIN Decoder Service", "vin-decoder-service", 8001),
        ("Fault Detector Service", "fault-detector-service", 8002),
        ("Diagnostic Service", "diagnostic-service", 8003),
        ("MQTT Bridge Service", "mqtt-bridge-service", 8004),
        ("API Gateway", "api-gateway", 8000),
    ]
    
    results = {}
    
    for service_name, service_dir, port in services:
        results[service_name] = test_service_startup(service_name, service_dir, port)
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    working_count = 0
    for service_name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{status} - {service_name}")
        if success:
            working_count += 1
    
    print(f"\n🎯 {working_count}/{len(services)} services working")
    
    if working_count == len(services):
        print("🎉 All microservices are functional!")
        print("💡 Ready to start full system integration")
    else:
        print("⚠️  Some services need attention")
        print("💡 Check individual service logs and dependencies")

if __name__ == "__main__":
    main()
