#!/usr/bin/env python3
"""
MOTOSPECT Microservices Demo
Shows the refactored system working independently
"""
import subprocess
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

class MicroserviceDemo:
    def __init__(self):
        self.processes = {}
        self.services = [
            {
                "name": "VIN Decoder Service",
                "dir": "services/vin-decoder-service", 
                "port": 8001,
                "test_endpoint": "/api/vin/info"
            },
            {
                "name": "Fault Detector Service",
                "dir": "services/fault-detector-service",
                "port": 8002, 
                "test_endpoint": "/api/fault/info"
            },
            {
                "name": "Diagnostic Service", 
                "dir": "services/diagnostic-service",
                "port": 8003,
                "test_endpoint": "/api/diagnostic/info"
            },
            {
                "name": "MQTT Bridge Service",
                "dir": "services/mqtt-bridge-service", 
                "port": 8004,
                "test_endpoint": "/api/mqtt/info"
            },
            {
                "name": "API Gateway",
                "dir": "services/api-gateway",
                "port": 8000,
                "test_endpoint": "/health"
            }
        ]

    def cleanup(self, signum=None, frame=None):
        """Clean up all processes"""
        print("\n🛑 Cleaning up services...")
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ Stopped {name}")
            except:
                try:
                    process.kill()
                except:
                    pass
        sys.exit(0)

    def start_service(self, service):
        """Start a single service"""
        try:
            import os
            env = os.environ.copy()
            env['PORT'] = str(service['port'])
            env['PYTHONPATH'] = f"{os.getcwd()}/backend:{env.get('PYTHONPATH', '')}"
            
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=service['dir'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[service['name']] = process
            time.sleep(2)
            
            if process.poll() is None:
                return True, "Started successfully"
            else:
                stdout, stderr = process.communicate()
                return False, f"Process died: {stderr.decode()[:200]}"
                
        except Exception as e:
            return False, str(e)

    def test_service(self, service):
        """Test if service is responding"""
        try:
            url = f"http://localhost:{service['port']}/health"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                # Try the specific test endpoint
                test_url = f"http://localhost:{service['port']}{service['test_endpoint']}"
                test_response = requests.get(test_url, timeout=3)
                return True, f"Health OK, Test endpoint: {test_response.status_code}"
            else:
                return False, f"Health check failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def demo_vin_functionality(self):
        """Demonstrate VIN decoding functionality"""
        print("\n🔧 VIN Functionality Demo:")
        try:
            # Test VIN validation
            response = requests.get("http://localhost:8001/api/vin/validate/1HGBH41JXMN109186", timeout=5)
            if response.status_code == 200:
                print("   ✅ VIN Validation working")
            
            # Test VIN decoding
            response = requests.get("http://localhost:8001/api/vin/decode/1HGBH41JXMN109186", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ VIN Decode: {data.get('make', 'Unknown')} {data.get('model', 'Unknown')}")
            
        except Exception as e:
            print(f"   ⚠️ VIN demo error: {e}")

    def demo_fault_functionality(self):
        """Demonstrate fault detection functionality"""
        print("\n🔍 Fault Detection Demo:")
        try:
            # Test fault analysis
            test_data = {
                "rpm": 2500,
                "coolant_temp": 95,
                "oil_pressure": 35,
                "fuel_pressure": 58
            }
            
            response = requests.post(
                "http://localhost:8002/api/fault/analyze", 
                json=test_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Fault Analysis: {len(data.get('faults', []))} issues detected")
            
        except Exception as e:
            print(f"   ⚠️ Fault demo error: {e}")

    def demo_api_gateway(self):
        """Demonstrate API Gateway routing"""
        print("\n🌐 API Gateway Demo:")
        try:
            # Test gateway routing to VIN service
            response = requests.get("http://localhost:8000/api/vin/validate/1HGBH41JXMN109186", timeout=5)
            if response.status_code == 200:
                print("   ✅ Gateway → VIN Service routing works")
                
            # Test gateway health aggregation
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                service_count = len(data.get('services', {}))
                print(f"   ✅ Gateway monitoring {service_count} services")
                
        except Exception as e:
            print(f"   ⚠️ Gateway demo error: {e}")

    def run_demo(self):
        """Run the complete microservices demo"""
        # Set up signal handler for cleanup
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        print("🚀 MOTOSPECT Microservices Demo")
        print("=" * 50)
        print("💡 This demonstrates the refactored architecture with:")
        print("   • Independent services with dynamic ports")
        print("   • Zero Docker complexity") 
        print("   • Isolated testing capability")
        print("   • Service-to-service communication")
        print("")

        # Start all services
        print("🔄 Starting microservices...")
        
        working_services = []
        
        for service in self.services:
            print(f"   Starting {service['name']}...", end="")
            success, message = self.start_service(service)
            
            if success:
                # Test the service
                test_success, test_message = self.test_service(service)
                if test_success:
                    print(f" ✅ Port {service['port']}")
                    working_services.append(service)
                else:
                    print(f" ⚠️ Started but not responding: {test_message}")
            else:
                print(f" ❌ {message}")

        if len(working_services) == 0:
            print("\n❌ No services started successfully")
            return

        print(f"\n📊 Status: {len(working_services)}/{len(self.services)} services running")

        # Wait a moment for full startup
        print("\n⏳ Waiting for services to initialize...")
        time.sleep(3)

        # Run functionality demos for working services
        if any(s['port'] == 8001 for s in working_services):
            self.demo_vin_functionality()
            
        if any(s['port'] == 8002 for s in working_services):
            self.demo_fault_functionality()
            
        if any(s['port'] == 8000 for s in working_services):
            self.demo_api_gateway()

        # Show service URLs
        print("\n🌐 Active Service URLs:")
        for service in working_services:
            print(f"   • {service['name']}: http://localhost:{service['port']}")

        print("\n🎯 Test Commands:")
        print("curl http://localhost:8001/api/vin/validate/1HGBH41JXMN109186")
        print("curl http://localhost:8000/health")
        
        print(f"\n🎉 Microservices Demo Complete!")
        print("💡 Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    demo = MicroserviceDemo()
    demo.run_demo()
