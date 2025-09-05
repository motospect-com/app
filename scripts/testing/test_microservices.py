#!/usr/bin/env python3
"""
Comprehensive test suite for MOTOSPECT microservices
Tests all microservices endpoints and functionality
"""

import sys
import time
import json
import asyncio
import httpx
from typing import Dict, List, Tuple, Any
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

class MicroservicesTestSuite:
    """Test suite for all MOTOSPECT microservices"""
    
    def __init__(self):
        self.base_urls = {
            "api-gateway": "http://localhost:8000",
            "vin-decoder": "http://localhost:8001",
            "fault-detector": "http://localhost:8002",
            "diagnostic": "http://localhost:8003",
            "mqtt-bridge": "http://localhost:8004"
        }
        self.test_results = []
        self.test_vin = "1HGBH41JXMN109186"
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
    def print_test(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = f"{Fore.GREEN}✅ PASSED" if passed else f"{Fore.RED}❌ FAILED"
        print(f"{status}{Style.RESET_ALL} - {test_name}")
        if details:
            print(f"    {Fore.YELLOW}Details: {details}{Style.RESET_ALL}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_health_endpoint(self, service_name: str, url: str) -> bool:
        """Test health endpoint of a service"""
        test_name = f"{service_name} Health Check"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") in ["healthy", "ok"]:
                        self.print_test(test_name, True, f"Response time: {response.elapsed.total_seconds():.3f}s")
                        return True
                    else:
                        self.print_test(test_name, False, f"Unhealthy status: {data.get('status')}")
                        return False
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
                    return False
        except Exception as e:
            self.print_test(test_name, False, str(e))
            return False
    
    async def test_all_health_endpoints(self):
        """Test health endpoints of all services"""
        self.print_header("Testing Health Endpoints")
        
        tasks = []
        for service_name, url in self.base_urls.items():
            tasks.append(self.test_health_endpoint(service_name, url))
        
        results = await asyncio.gather(*tasks)
        return all(results)
    
    async def test_vin_decoder_service(self):
        """Test VIN Decoder Service endpoints"""
        self.print_header("Testing VIN Decoder Service")
        
        base_url = self.base_urls["vin-decoder"]
        
        # Test VIN validation - valid VIN
        test_name = "VIN Validation (Valid)"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/vin/validate/{self.test_vin}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid") == True:
                        self.print_test(test_name, True, f"VIN: {data.get('vin')}")
                    else:
                        self.print_test(test_name, False, f"VIN marked as invalid: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test VIN validation - invalid VIN
        test_name = "VIN Validation (Invalid)"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/vin/validate/INVALID123")
                data = response.json()
                if data.get("valid") == False:
                    self.print_test(test_name, True, f"Error: {data.get('error')}")
                else:
                    self.print_test(test_name, False, "Invalid VIN not detected")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test VIN decoding
        test_name = "VIN Decoding"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/vin/decode/{self.test_vin}")
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["vin", "make", "model", "year"]
                    if all(field in data for field in required_fields):
                        self.print_test(test_name, True, f"{data.get('make')} {data.get('model')} ({data.get('year')})")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test VIN recalls
        test_name = "VIN Recalls"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/vin/recalls/{self.test_vin}")
                if response.status_code == 200:
                    data = response.json()
                    if "recalls" in data and "total_recalls" in data:
                        self.print_test(test_name, True, f"Total recalls: {data.get('total_recalls')}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    async def test_fault_detector_service(self):
        """Test Fault Detector Service endpoints"""
        self.print_header("Testing Fault Detector Service")
        
        base_url = self.base_urls["fault-detector"]
        
        # Test fault analysis
        test_name = "Fault Analysis"
        try:
            async with httpx.AsyncClient() as client:
                test_data = {
                    "rpm": 2500,
                    "coolant_temp": 85,
                    "oil_pressure": 40,
                    "fuel_pressure": 45
                }
                response = await client.post(f"{base_url}/api/fault/analyze", json=test_data)
                if response.status_code == 200:
                    data = response.json()
                    if "faults" in data and "health_score" in data:
                        self.print_test(test_name, True, f"Health score: {data.get('health_score')}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test fault codes
        test_name = "Fault Codes Retrieval"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/fault/codes")
                if response.status_code == 200:
                    data = response.json()
                    if "codes" in data and "definitions" in data:
                        self.print_test(test_name, True, f"Codes found: {len(data.get('codes', []))}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    async def test_diagnostic_service(self):
        """Test Diagnostic Service endpoints"""
        self.print_header("Testing Diagnostic Service")
        
        base_url = self.base_urls["diagnostic"]
        
        # Test report generation
        test_name = "Diagnostic Report Generation"
        try:
            async with httpx.AsyncClient() as client:
                test_data = {
                    "vin": self.test_vin,
                    "mileage": 50000
                }
                response = await client.post(f"{base_url}/api/diagnostic/report", json=test_data)
                if response.status_code == 200:
                    data = response.json()
                    if "report_id" in data and "vehicle_health" in data:
                        health = data.get("vehicle_health", {})
                        self.print_test(test_name, True, 
                                      f"Report ID: {data.get('report_id')}, Overall: {health.get('overall_score')}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test diagnostic summary
        test_name = "Diagnostic Summary"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/diagnostic/summary")
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["total_diagnostics", "active_issues"]
                    if all(field in data for field in required_fields):
                        self.print_test(test_name, True, 
                                      f"Total: {data.get('total_diagnostics')}, Active: {data.get('active_issues')}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    async def test_mqtt_bridge_service(self):
        """Test MQTT Bridge Service endpoints"""
        self.print_header("Testing MQTT Bridge Service")
        
        base_url = self.base_urls["mqtt-bridge"]
        
        # Test MQTT status
        test_name = "MQTT Status"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/mqtt/status")
                if response.status_code == 200:
                    data = response.json()
                    if "connected" in data and "active_topics" in data:
                        self.print_test(test_name, True, 
                                      f"Connected: {data.get('connected')}, Topics: {len(data.get('active_topics', []))}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test MQTT publish
        test_name = "MQTT Publish"
        try:
            async with httpx.AsyncClient() as client:
                test_data = {
                    "topic": "vehicle/test",
                    "message": "test_message"
                }
                response = await client.post(f"{base_url}/api/mqtt/publish", json=test_data)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "published":
                        self.print_test(test_name, True, f"Message ID: {data.get('message_id')}")
                    else:
                        self.print_test(test_name, False, f"Unexpected status: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test MQTT subscribe
        test_name = "MQTT Subscribe"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/mqtt/subscribe/vehicle/sensors")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "subscribed":
                        self.print_test(test_name, True, f"Subscription ID: {data.get('subscription_id')}")
                    else:
                        self.print_test(test_name, False, f"Unexpected status: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    async def test_api_gateway(self):
        """Test API Gateway routing and aggregation"""
        self.print_header("Testing API Gateway")
        
        base_url = self.base_urls["api-gateway"]
        
        # Test services status
        test_name = "Services Status Endpoint"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{base_url}/services/status")
                if response.status_code == 200:
                    data = response.json()
                    healthy_services = sum(1 for s in data.values() if s.get("status") == "healthy")
                    total_services = len(data)
                    if healthy_services == total_services:
                        self.print_test(test_name, True, f"All {total_services} services healthy")
                    else:
                        self.print_test(test_name, False, f"Only {healthy_services}/{total_services} healthy")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test VIN decode through gateway
        test_name = "VIN Decode via Gateway"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/vin/decode/{self.test_vin}")
                if response.status_code == 200:
                    data = response.json()
                    if "vin" in data and "make" in data:
                        self.print_test(test_name, True, "VIN decoded successfully")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test fault analysis through gateway
        test_name = "Fault Analysis via Gateway"
        try:
            async with httpx.AsyncClient() as client:
                test_data = {"rpm": 3000, "temp": 90}
                response = await client.post(f"{base_url}/api/fault/analyze", json=test_data)
                if response.status_code == 200:
                    data = response.json()
                    if "health_score" in data:
                        self.print_test(test_name, True, f"Health score: {data.get('health_score')}")
                    else:
                        self.print_test(test_name, False, f"Missing fields: {data}")
                else:
                    self.print_test(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    async def test_performance(self):
        """Test performance and response times"""
        self.print_header("Testing Performance")
        
        # Test concurrent requests
        test_name = "Concurrent Requests (10 simultaneous)"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                urls = [
                    f"{self.base_urls['api-gateway']}/health",
                    f"{self.base_urls['vin-decoder']}/health",
                    f"{self.base_urls['fault-detector']}/health",
                    f"{self.base_urls['diagnostic']}/health",
                    f"{self.base_urls['mqtt-bridge']}/health",
                ] * 2  # 10 total requests
                
                start_time = time.time()
                tasks = [client.get(url) for url in urls]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                
                successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
                total_time = end_time - start_time
                
                if successful == len(urls):
                    self.print_test(test_name, True, f"All requests successful in {total_time:.3f}s")
                else:
                    self.print_test(test_name, False, f"Only {successful}/{len(urls)} successful")
        except Exception as e:
            self.print_test(test_name, False, str(e))
        
        # Test response time
        test_name = "Average Response Time"
        try:
            response_times = []
            async with httpx.AsyncClient() as client:
                for service_name, url in self.base_urls.items():
                    response = await client.get(f"{url}/health")
                    response_times.append(response.elapsed.total_seconds())
            
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            if avg_time < 0.5:  # Average should be under 500ms
                self.print_test(test_name, True, f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
            else:
                self.print_test(test_name, False, f"Too slow - Avg: {avg_time:.3f}s")
        except Exception as e:
            self.print_test(test_name, False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n{Fore.WHITE}Total Tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {passed_tests}")
        print(f"{Fore.RED}Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"  - {test['test']}: {test['details']}")
        
        # Success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate == 100:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! (100%){Style.RESET_ALL}")
        elif success_rate >= 80:
            print(f"\n{Fore.YELLOW}⚠️  Success Rate: {success_rate:.1f}%{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Success Rate: {success_rate:.1f}%{Style.RESET_ALL}")
        
        return success_rate == 100
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}MOTOSPECT Microservices Test Suite")
        print(f"{Fore.CYAN}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Run tests in order
        await self.test_all_health_endpoints()
        await self.test_vin_decoder_service()
        await self.test_fault_detector_service()
        await self.test_diagnostic_service()
        await self.test_mqtt_bridge_service()
        await self.test_api_gateway()
        await self.test_performance()
        
        # Print summary
        all_passed = self.print_summary()
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results,
                "summary": {
                    "total": len(self.test_results),
                    "passed": sum(1 for t in self.test_results if t["passed"]),
                    "failed": sum(1 for t in self.test_results if not t["passed"])
                }
            }, f, indent=2)
        
        print(f"\n{Fore.YELLOW}Results saved to test_results.json{Style.RESET_ALL}")
        
        return all_passed


async def main():
    """Main function"""
    test_suite = MicroservicesTestSuite()
    all_passed = await test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test suite failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
