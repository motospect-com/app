#!/usr/bin/env python3
"""
Comprehensive test suite for all MOTOSPECT microservices
Tests all endpoints and verifies functionality
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class ServiceTester:
    """Test all MOTOSPECT microservices"""
    
    def __init__(self):
        self.services = {
            "API Gateway": "http://localhost:8000",
            "VIN Decoder": "http://localhost:8001",
            "Fault Detector": "http://localhost:8002",
            "Diagnostic": "http://localhost:8003",
            "MQTT Bridge": "http://localhost:8004"
        }
        self.test_results = []
        self.test_vin = "1HGBH41JXMN109186"
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.CYAN}{'='*60}")
        print(f"{text}")
        print(f"{'='*60}{Colors.RESET}")
    
    def test_result(self, test_name: str, success: bool, details: str = ""):
        """Record and print test result"""
        status = f"{Colors.GREEN}✅ PASS" if success else f"{Colors.RED}❌ FAIL"
        print(f"{status}{Colors.RESET} - {test_name}")
        if details:
            print(f"    {Colors.YELLOW}→ {details}{Colors.RESET}")
        
        self.test_results.append({
            "test": test_name,
            "passed": success,
            "details": details
        })
        
        return success
    
    def test_health_endpoints(self) -> bool:
        """Test health endpoints of all services"""
        self.print_header("Testing Health Endpoints")
        
        all_healthy = True
        for service_name, url in self.services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.test_result(f"{service_name} Health", True, 
                                   f"Status: {data.get('status', 'unknown')}")
                else:
                    self.test_result(f"{service_name} Health", False, 
                                   f"HTTP {response.status_code}")
                    all_healthy = False
            except requests.exceptions.RequestException as e:
                self.test_result(f"{service_name} Health", False, 
                               f"Connection error: {str(e)[:50]}")
                all_healthy = False
        
        return all_healthy
    
    def test_vin_decoder(self) -> bool:
        """Test VIN Decoder Service"""
        self.print_header("Testing VIN Decoder Service")
        
        base_url = self.services["VIN Decoder"]
        all_passed = True
        
        # Test VIN validation - valid
        try:
            response = requests.get(f"{base_url}/api/vin/validate/{self.test_vin}")
            if response.status_code == 200:
                data = response.json()
                passed = data.get("valid") == True
                self.test_result("VIN Validation (Valid)", passed,
                               f"VIN: {data.get('vin', 'N/A')}")
                all_passed = all_passed and passed
            else:
                self.test_result("VIN Validation (Valid)", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("VIN Validation (Valid)", False, str(e)[:50])
            all_passed = False
        
        # Test VIN validation - invalid
        try:
            response = requests.get(f"{base_url}/api/vin/validate/INVALID123")
            data = response.json()
            passed = data.get("valid") == False
            self.test_result("VIN Validation (Invalid)", passed,
                           f"Error detected: {data.get('error', 'N/A')}")
            all_passed = all_passed and passed
        except Exception as e:
            self.test_result("VIN Validation (Invalid)", False, str(e)[:50])
            all_passed = False
        
        # Test VIN decoding
        try:
            response = requests.get(f"{base_url}/api/vin/decode/{self.test_vin}")
            if response.status_code == 200:
                data = response.json()
                has_fields = all(k in data for k in ["vin", "make", "model", "year"])
                self.test_result("VIN Decoding", has_fields,
                               f"{data.get('make')} {data.get('model')} ({data.get('year')})")
                all_passed = all_passed and has_fields
            else:
                self.test_result("VIN Decoding", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("VIN Decoding", False, str(e)[:50])
            all_passed = False
        
        # Test VIN recalls
        try:
            response = requests.get(f"{base_url}/api/vin/recalls/{self.test_vin}")
            if response.status_code == 200:
                data = response.json()
                has_fields = "recalls" in data and "total_recalls" in data
                self.test_result("VIN Recalls", has_fields,
                               f"Total recalls: {data.get('total_recalls', 'N/A')}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("VIN Recalls", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("VIN Recalls", False, str(e)[:50])
            all_passed = False
        
        return all_passed
    
    def test_fault_detector(self) -> bool:
        """Test Fault Detector Service"""
        self.print_header("Testing Fault Detector Service")
        
        base_url = self.services["Fault Detector"]
        all_passed = True
        
        # Test fault analysis
        try:
            test_data = {
                "rpm": 2500,
                "coolant_temp": 85,
                "oil_pressure": 40
            }
            response = requests.post(f"{base_url}/api/fault/analyze", json=test_data)
            if response.status_code == 200:
                data = response.json()
                has_fields = "health_score" in data and "faults" in data
                self.test_result("Fault Analysis", has_fields,
                               f"Health score: {data.get('health_score', 'N/A')}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("Fault Analysis", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Fault Analysis", False, str(e)[:50])
            all_passed = False
        
        # Test fault codes
        try:
            response = requests.get(f"{base_url}/api/fault/codes")
            if response.status_code == 200:
                data = response.json()
                has_fields = "codes" in data and "definitions" in data
                self.test_result("Fault Codes", has_fields,
                               f"Codes found: {len(data.get('codes', []))}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("Fault Codes", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Fault Codes", False, str(e)[:50])
            all_passed = False
        
        return all_passed
    
    def test_diagnostic_service(self) -> bool:
        """Test Diagnostic Service"""
        self.print_header("Testing Diagnostic Service")
        
        base_url = self.services["Diagnostic"]
        all_passed = True
        
        # Test report generation
        try:
            test_data = {"vin": self.test_vin, "mileage": 50000}
            response = requests.post(f"{base_url}/api/diagnostic/report", json=test_data)
            if response.status_code == 200:
                data = response.json()
                has_fields = "report_id" in data and "vehicle_health" in data
                health = data.get("vehicle_health", {})
                self.test_result("Diagnostic Report", has_fields,
                               f"Report ID: {data.get('report_id')}, Overall: {health.get('overall_score')}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("Diagnostic Report", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Diagnostic Report", False, str(e)[:50])
            all_passed = False
        
        # Test diagnostic summary
        try:
            response = requests.get(f"{base_url}/api/diagnostic/summary")
            if response.status_code == 200:
                data = response.json()
                has_fields = "total_diagnostics" in data and "active_issues" in data
                self.test_result("Diagnostic Summary", has_fields,
                               f"Total: {data.get('total_diagnostics')}, Active: {data.get('active_issues')}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("Diagnostic Summary", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Diagnostic Summary", False, str(e)[:50])
            all_passed = False
        
        return all_passed
    
    def test_mqtt_bridge(self) -> bool:
        """Test MQTT Bridge Service"""
        self.print_header("Testing MQTT Bridge Service")
        
        base_url = self.services["MQTT Bridge"]
        all_passed = True
        
        # Test MQTT status
        try:
            response = requests.get(f"{base_url}/api/mqtt/status")
            if response.status_code == 200:
                data = response.json()
                has_fields = "connected" in data and "active_topics" in data
                self.test_result("MQTT Status", has_fields,
                               f"Connected: {data.get('connected')}, Topics: {len(data.get('active_topics', []))}")
                all_passed = all_passed and has_fields
            else:
                self.test_result("MQTT Status", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("MQTT Status", False, str(e)[:50])
            all_passed = False
        
        # Test MQTT publish
        try:
            test_data = {"topic": "vehicle/test", "message": "test_message"}
            response = requests.post(f"{base_url}/api/mqtt/publish", json=test_data)
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "published"
                self.test_result("MQTT Publish", success,
                               f"Message ID: {data.get('message_id')}")
                all_passed = all_passed and success
            else:
                self.test_result("MQTT Publish", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("MQTT Publish", False, str(e)[:50])
            all_passed = False
        
        # Test MQTT subscribe
        try:
            response = requests.get(f"{base_url}/api/mqtt/subscribe/vehicle/sensors")
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "subscribed"
                self.test_result("MQTT Subscribe", success,
                               f"Subscription ID: {data.get('subscription_id')}")
                all_passed = all_passed and success
            else:
                self.test_result("MQTT Subscribe", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("MQTT Subscribe", False, str(e)[:50])
            all_passed = False
        
        return all_passed
    
    def test_api_gateway(self) -> bool:
        """Test API Gateway routing"""
        self.print_header("Testing API Gateway")
        
        base_url = self.services["API Gateway"]
        all_passed = True
        
        # Test service status endpoint
        try:
            response = requests.get(f"{base_url}/services/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                healthy = sum(1 for s in data.values() if s.get("status") == "healthy")
                total = len(data)
                success = healthy == total
                self.test_result("Services Status", success,
                               f"{healthy}/{total} services healthy")
                all_passed = all_passed and success
            else:
                self.test_result("Services Status", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Services Status", False, str(e)[:50])
            all_passed = False
        
        # Test VIN decode through gateway
        try:
            response = requests.get(f"{base_url}/api/vin/decode/{self.test_vin}")
            if response.status_code == 200:
                data = response.json()
                success = "vin" in data and "make" in data
                self.test_result("Gateway VIN Routing", success,
                               "VIN decoded via gateway")
                all_passed = all_passed and success
            else:
                self.test_result("Gateway VIN Routing", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Gateway VIN Routing", False, str(e)[:50])
            all_passed = False
        
        # Test fault analysis through gateway
        try:
            test_data = {"rpm": 3000, "temp": 90}
            response = requests.post(f"{base_url}/api/fault/analyze", json=test_data)
            if response.status_code == 200:
                data = response.json()
                success = "health_score" in data
                self.test_result("Gateway Fault Routing", success,
                               f"Health: {data.get('health_score')}")
                all_passed = all_passed and success
            else:
                self.test_result("Gateway Fault Routing", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.test_result("Gateway Fault Routing", False, str(e)[:50])
            all_passed = False
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test response times and performance"""
        self.print_header("Testing Performance")
        
        all_passed = True
        
        # Test response times
        response_times = []
        for service_name, url in self.services.items():
            try:
                start = time.time()
                response = requests.get(f"{url}/health", timeout=5)
                elapsed = time.time() - start
                response_times.append(elapsed)
                
                passed = elapsed < 1.0  # Should respond within 1 second
                self.test_result(f"{service_name} Response Time", passed,
                               f"{elapsed:.3f}s")
                all_passed = all_passed and passed
            except Exception as e:
                self.test_result(f"{service_name} Response Time", False, str(e)[:50])
                all_passed = False
        
        # Average response time
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            passed = avg_time < 0.5  # Average should be under 500ms
            self.test_result("Average Response Time", passed,
                           f"{avg_time:.3f}s")
            all_passed = all_passed and passed
        
        return all_passed
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if failed > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")
        
        if success_rate == 100:
            print(f"{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.RESET}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}⚠️  Some tests failed{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Multiple test failures{Colors.RESET}")
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": success_rate
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n{Colors.CYAN}Results saved to test_results.json{Colors.RESET}")
        
        return success_rate == 100
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("="*60)
        print("MOTOSPECT Microservices Test Suite")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"{Colors.RESET}")
        
        # Run test suites
        self.test_health_endpoints()
        self.test_vin_decoder()
        self.test_fault_detector()
        self.test_diagnostic_service()
        self.test_mqtt_bridge()
        self.test_api_gateway()
        self.test_performance()
        
        # Print summary
        all_passed = self.print_summary()
        
        return all_passed


def main():
    """Main function"""
    tester = ServiceTester()
    
    try:
        all_passed = tester.run_all_tests()
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
