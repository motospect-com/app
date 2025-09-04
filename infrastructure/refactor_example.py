#!/usr/bin/env python3
"""
Practical Example: Refaktoryzacja MOTOSPECT
Demonstracja jak podzielić monolityczną aplikację na mikroserwisy
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from service_manager import ServiceManager, ServiceConfig
from mqtt_service_bus import MQTTServiceBus, VINDecoderMQTTService
from testing_framework import TestRunner, VINDecoderServiceTest

class MotospectRefactorDemo:
    """Demo refaktoryzacji MOTOSPECT na mikroserwisy"""
    
    def __init__(self):
        self.service_manager = ServiceManager()
        self.mqtt_bus = MQTTServiceBus()
        
    def setup_microservices(self):
        """Setup mikroserwisów"""
        print("🏗️ Setting up MOTOSPECT microservices...")
        
        # 1. VIN Decoder Service
        vin_service = ServiceConfig(
            name="vin-decoder",
            command=["python3", "-c", """
import sys
sys.path.append('../infrastructure')
from mqtt_service_bus import MQTTServiceBus, VINDecoderMQTTService
import time

bus = MQTTServiceBus()
if bus.connect():
    service = VINDecoderMQTTService(bus)
    print("✅ VIN Decoder Service running")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.disconnect()
            """],
            working_dir=str(Path(__file__).parent),
            environment={"PYTHONPATH": str(Path(__file__).parent)}
        )
        
        # 2. API Gateway
        gateway_service = ServiceConfig(
            name="api-gateway",
            command=["python3", "-c", self._get_gateway_code()],
            working_dir=str(Path(__file__).parent),
            environment={"PYTHONPATH": str(Path(__file__).parent)}
        )
        
        # 3. Frontend Service  
        frontend_service = ServiceConfig(
            name="frontend",
            command=["python3", "-c", self._get_frontend_code()],
            working_dir=str(Path(__file__).parent)
        )
        
        # Register services
        services = [vin_service, gateway_service, frontend_service]
        for service in services:
            self.service_manager.register_service(service)
            
        return services
    
    def _get_gateway_code(self):
        """API Gateway kod"""
        return '''
import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mqtt_service_bus import MQTTServiceBus
from http.server import HTTPServer, BaseHTTPRequestHandler

class APIGateway(BaseHTTPRequestHandler):
    mqtt_bus = None
    
    def do_GET(self):
        if self.path.startswith('/api/vin/decode/'):
            vin = self.path.split('/')[-1]
            try:
                # Call VIN decoder service via MQTT
                result = self.mqtt_bus.call_service('vin-decoder', 'decode', {'vin': vin})
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')  
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy', 'service': 'api-gateway'}).encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

# Setup MQTT connection
mqtt_bus = MQTTServiceBus()
if mqtt_bus.connect():
    APIGateway.mqtt_bus = mqtt_bus
    print("✅ API Gateway running on port 8080")
    server = HTTPServer(('0.0.0.0', 8080), APIGateway)
    server.serve_forever()
        '''
    
    def _get_frontend_code(self):
        """Simple frontend kod"""
        return '''
import http.server
import json

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>MOTOSPECT - Microservices Demo</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        input, button { padding: 10px; margin: 5px; }
        .result { background: #f0f0f0; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 MOTOSPECT Microservices Demo</h1>
        <div>
            <input type="text" id="vin" placeholder="Enter VIN (e.g., 1HGCM82633A123456)" size="30">
            <button onclick="decodeVin()">Decode VIN</button>
        </div>
        <div id="result" class="result" style="display:none;"></div>
    </div>
    
    <script>
    async function decodeVin() {
        const vin = document.getElementById('vin').value;
        const resultDiv = document.getElementById('result');
        
        if (!vin) {
            alert('Please enter a VIN');
            return;
        }
        
        try {
            const response = await fetch(`http://localhost:8080/api/vin/decode/${vin}`);
            const data = await response.json();
            
            resultDiv.innerHTML = `
                <h3>VIN Decode Result:</h3>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `;
            resultDiv.style.display = 'block';
        } catch (error) {
            resultDiv.innerHTML = `<h3>Error:</h3><p>${error.message}</p>`;
            resultDiv.style.display = 'block';
        }
    }
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode())
        else:
            super().do_GET()

print("✅ Frontend running on port 3000")
server = http.server.HTTPServer(('0.0.0.0', 3000), FrontendHandler)
server.serve_forever()
        '''
    
    def start_mqtt_broker(self):
        """Start MQTT broker (Mosquitto)"""
        print("🦟 Starting MQTT broker...")
        try:
            # Try to start mosquitto if available
            subprocess.run(['mosquitto', '-d'], check=False)
            time.sleep(2)
            print("✅ MQTT broker (Mosquitto) started")
            return True
        except FileNotFoundError:
            print("⚠️ Mosquitto not found, using embedded broker simulation")
            # In real scenario, you would use an embedded MQTT broker
            return True
    
    def run_demo(self):
        """Uruchomienie kompletnego demo"""
        print("🚀 Starting MOTOSPECT Microservices Demo")
        print("="*50)
        
        # 1. Start MQTT broker
        if not self.start_mqtt_broker():
            print("❌ Failed to start MQTT broker")
            return False
        
        # 2. Setup services  
        services = self.setup_microservices()
        
        # 3. Start services
        print("\n📋 Starting services...")
        for service in services:
            if self.service_manager.start_service(service.name):
                print(f"✅ {service.name} started")
            else:
                print(f"❌ {service.name} failed to start")
        
        # 4. Show service status
        print("\n📊 Service Status:")
        print("-" * 40)
        all_services = self.service_manager.list_all_services()
        for service in all_services:
            status_emoji = "✅" if service.get("healthy") else "❌" if service["status"] == "running" else "🛑"
            print(f"{status_emoji} {service['name']:15} {service['status']:10} Port: {service.get('port', 'N/A')}")
        
        # 5. Demo endpoints
        print("\n🌐 Available Endpoints:")
        print("- Frontend:     http://localhost:3000")
        print("- API Gateway:  http://localhost:8080")
        print("- Health Check: http://localhost:8080/health")
        print("- VIN Decode:   http://localhost:8080/api/vin/decode/1HGCM82633A123456")
        
        print("\n✨ Demo running! Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(5)
                # Periodic health check
                healthy_services = [s for s in self.service_manager.list_all_services() if s.get("healthy")]
                print(f"💚 {len(healthy_services)}/{len(all_services)} services healthy")
        except KeyboardInterrupt:
            print("\n🛑 Stopping demo...")
            self.stop_demo()
    
    def stop_demo(self):
        """Zatrzymanie demo"""
        print("🔄 Stopping all services...")
        for service_info in self.service_manager.registry.list_services():
            self.service_manager.stop_service(service_info.config.name)
        
        if hasattr(self, 'mqtt_bus'):
            self.mqtt_bus.disconnect()
        
        print("✅ Demo stopped")
    
    def run_tests(self):
        """Uruchomienie testów mikroserwisów"""
        print("🧪 Running microservices tests...")
        
        runner = TestRunner()
        
        # Test VIN Decoder service
        print("\n1. Testing VIN Decoder Service:")
        vin_results = runner.run_service_tests(VINDecoderServiceTest)
        
        # Summary
        passed = sum(1 for r in vin_results.values() if r['status'] == 'PASSED')
        total = len(vin_results)
        
        print(f"\n📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed")
            return False

class ComparisonDemo:
    """Porównanie różnych architektur komunikacji"""
    
    def compare_communication_protocols(self):
        """Porównanie REST API vs MQTT vs gRPC"""
        print("\n📊 Communication Protocols Comparison")
        print("="*50)
        
        protocols = [
            {
                'name': 'REST API',
                'latency': '50-200ms',
                'throughput': 'Medium',
                'complexity': 'Low',
                'scalability': 'Medium',
                'use_case': 'CRUD operations, API Gateway'
            },
            {
                'name': 'MQTT',
                'latency': '5-50ms',
                'throughput': 'High',
                'complexity': 'Medium',
                'scalability': 'High',
                'use_case': 'IoT sensors, async events'
            },
            {
                'name': 'gRPC',
                'latency': '1-10ms',
                'throughput': 'Very High',
                'complexity': 'High',
                'scalability': 'Very High',
                'use_case': 'Service-to-service calls'
            }
        ]
        
        # Print comparison table
        headers = ['Protocol', 'Latency', 'Throughput', 'Complexity', 'Scalability', 'Best Use Case']
        print(f"{'Protocol':<10} {'Latency':<12} {'Throughput':<12} {'Complexity':<12} {'Scalability':<12} {'Use Case':<25}")
        print("-" * 90)
        
        for p in protocols:
            print(f"{p['name']:<10} {p['latency']:<12} {p['throughput']:<12} {p['complexity']:<12} {p['scalability']:<12} {p['use_case']:<25}")
        
        print(f"\n💡 Recommendation for MOTOSPECT:")
        print("- API Gateway: REST API (external facing)")
        print("- Inter-service: MQTT (async, scalable)")
        print("- IoT Data: MQTT (vehicle sensors)")
        print("- Real-time: WebSockets (dashboard updates)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python refactor_example.py [demo|test|compare]")
        print("  demo     - Run microservices demo")  
        print("  test     - Run service tests")
        print("  compare  - Compare communication protocols")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "demo":
        demo = MotospectRefactorDemo()
        demo.run_demo()
        
    elif command == "test":
        demo = MotospectRefactorDemo()
        success = demo.run_tests()
        sys.exit(0 if success else 1)
        
    elif command == "compare":
        comparison = ComparisonDemo()
        comparison.compare_communication_protocols()
        
    else:
        print("Unknown command. Use: demo, test, or compare")
        sys.exit(1)
