#!/usr/bin/env python3
"""
Testing Framework dla pojedynczych serwisów MOTOSPECT
Rozwiązuje problemy z testowaniem izolowanych komponentów
"""
import asyncio
import json
import subprocess
import time
import requests
import pytest
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager
from unittest.mock import Mock, patch
import tempfile
import threading
from pathlib import Path

@dataclass
class TestServiceConfig:
    name: str
    port: int
    start_command: List[str]
    working_dir: str
    health_endpoint: str = "/health"
    startup_timeout: int = 30

class MockServiceRegistry:
    """Registry for mock services used in testing"""
    
    def __init__(self):
        self.mocks: Dict[str, Mock] = {}
        self.responses: Dict[str, Dict[str, Any]] = {}
    
    def register_mock(self, service_name: str, responses: Dict[str, Any]):
        """Register mock responses for a service"""
        self.responses[service_name] = responses
        self.mocks[service_name] = Mock()
        
        # Configure mock responses
        for endpoint, response in responses.items():
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]  # Remove leading slash
            getattr(self.mocks[service_name], endpoint.replace('/', '_')).return_value = response
    
    def get_mock_response(self, service_name: str, endpoint: str) -> Any:
        """Get mock response for service endpoint"""
        return self.responses.get(service_name, {}).get(endpoint, {"error": "Mock not found"})

class TestServiceCluster:
    """Manages cluster of services for integration testing"""
    
    def __init__(self, services: List[TestServiceConfig]):
        self.services = {svc.name: svc for svc in services}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.base_port = 9000
        
    def start_all(self):
        """Start all services in dependency order"""
        for service_name, config in self.services.items():
            self.start_service(service_name)
    
    def start_service(self, service_name: str) -> bool:
        """Start individual service"""
        config = self.services[service_name]
        
        try:
            # Set PORT environment variable
            env = os.environ.copy()
            env['PORT'] = str(config.port)
            
            process = subprocess.Popen(
                config.start_command,
                cwd=config.working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[service_name] = process
            
            # Wait for service to be ready
            if self._wait_for_service(service_name, config):
                print(f"✅ Test service {service_name} started on port {config.port}")
                return True
            else:
                print(f"❌ Test service {service_name} failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting test service {service_name}: {e}")
            return False
    
    def stop_all(self):
        """Stop all running services"""
        for service_name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        self.processes.clear()
    
    def _wait_for_service(self, service_name: str, config: TestServiceConfig) -> bool:
        """Wait for service to respond to health checks"""
        health_url = f"http://localhost:{config.port}{config.health_endpoint}"
        
        for _ in range(config.startup_timeout):
            try:
                response = requests.get(health_url, timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        return False
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL"""
        config = self.services[service_name]
        return f"http://localhost:{config.port}"

class ServiceTestCase:
    """Base class for individual service testing"""
    
    def __init__(self, service_config: TestServiceConfig):
        self.service_config = service_config
        self.service_url = f"http://localhost:{service_config.port}"
        self.mock_registry = MockServiceRegistry()
        self.cluster = None
    
    def setup_method(self):
        """Setup for each test method"""
        self.cluster = TestServiceCluster([self.service_config])
        self.cluster.start_all()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if self.cluster:
            self.cluster.stop_all()
    
    def mock_dependency(self, service_name: str, responses: Dict[str, Any]):
        """Mock external service dependency"""
        self.mock_registry.register_mock(service_name, responses)
    
    @contextmanager
    def mock_external_api(self, api_name: str, responses: Dict[str, Any]):
        """Context manager for mocking external APIs"""
        with patch(f'requests.get') as mock_get:
            def side_effect(url, **kwargs):
                for endpoint, response in responses.items():
                    if endpoint in url:
                        mock_response = Mock()
                        mock_response.json.return_value = response
                        mock_response.status_code = 200
                        return mock_response
                raise requests.RequestException(f"Unmocked URL: {url}")
            
            mock_get.side_effect = side_effect
            yield mock_get

class IntegrationTestSuite:
    """Integration test suite for multiple services"""
    
    def __init__(self, service_configs: List[TestServiceConfig]):
        self.service_configs = service_configs
        self.cluster = TestServiceCluster(service_configs)
    
    def setup_class(self):
        """Setup once for all integration tests"""
        self.cluster.start_all()
    
    def teardown_class(self):
        """Cleanup after all integration tests"""
        self.cluster.stop_all()
    
    def test_service_communication(self, source_service: str, target_service: str, endpoint: str):
        """Test communication between services"""
        source_url = self.cluster.get_service_url(source_service)
        target_url = self.cluster.get_service_url(target_service)
        
        # Test that source can reach target
        response = requests.get(f"{target_url}{endpoint}")
        return response.status_code == 200

# Specific test cases for MOTOSPECT services
class VINDecoderServiceTest(ServiceTestCase):
    
    def __init__(self):
        super().__init__(TestServiceConfig(
            name="vin-decoder",
            port=9001,
            start_command=["python3", "vin_decoder_service.py"],
            working_dir="../services/vin-decoder"
        ))
    
    def test_health_endpoint(self):
        """Test service health endpoint"""
        response = requests.get(f"{self.service_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_vin_decode_valid(self):
        """Test VIN decoding with valid VIN"""
        vin = "1HGCM82633A123456"
        
        with self.mock_external_api("nhtsa-api", {
            "decode": {
                "Results": [{
                    "Make": "Honda",
                    "Model": "Civic", 
                    "ModelYear": "2003"
                }]
            }
        }):
            response = requests.get(f"{self.service_url}/api/vin/decode/{vin}")
            assert response.status_code == 200
            data = response.json()
            assert data['vin'] == vin
            assert 'decoded' in data
    
    def test_vin_decode_invalid(self):
        """Test VIN decoding with invalid VIN"""
        invalid_vin = "INVALID"
        response = requests.get(f"{self.service_url}/api/vin/decode/{invalid_vin}")
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

class DiagnosticServiceTest(ServiceTestCase):
    
    def __init__(self):
        super().__init__(TestServiceConfig(
            name="diagnostic-service",
            port=9002,
            start_command=["python3", "diagnostic_service.py"],
            working_dir="../services/diagnostic"
        ))
    
    def test_generate_report(self):
        """Test diagnostic report generation"""
        # Mock VIN decoder dependency
        self.mock_dependency("vin-decoder", {
            "/decode/1HGCM82633A123456": {
                "vin": "1HGCM82633A123456",
                "decoded": {"make": "Honda", "model": "Civic"}
            }
        })
        
        payload = {
            "vin": "1HGCM82633A123456",
            "obd_data": {
                "rpm": 2500,
                "coolant_temp": 85,
                "oil_pressure": 35
            }
        }
        
        response = requests.post(f"{self.service_url}/api/report/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'report_id' in data
        assert 'health_score' in data

class MotospectIntegrationTest(IntegrationTestSuite):
    """Full integration tests for MOTOSPECT services"""
    
    def __init__(self):
        services = [
            TestServiceConfig(
                name="vin-decoder",
                port=9001,
                start_command=["python3", "vin_decoder_service.py"],
                working_dir="../services/vin-decoder"
            ),
            TestServiceConfig(
                name="diagnostic-service", 
                port=9002,
                start_command=["python3", "diagnostic_service.py"],
                working_dir="../services/diagnostic"
            ),
            TestServiceConfig(
                name="api-gateway",
                port=9000,
                start_command=["python3", "gateway.py"],
                working_dir="../services/api-gateway"
            )
        ]
        super().__init__(services)
    
    def test_end_to_end_diagnosis(self):
        """Test complete diagnosis workflow"""
        gateway_url = self.cluster.get_service_url("api-gateway")
        
        # Test complete workflow through API Gateway
        payload = {
            "vin": "1HGCM82633A123456",
            "obd_data": {
                "rpm": 2500,
                "coolant_temp": 85,
                "oil_pressure": 35,
                "fault_codes": ["P0301"]
            }
        }
        
        response = requests.post(f"{gateway_url}/api/v1/diagnose", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert 'vehicle_info' in data
        assert 'diagnostic_report' in data
        assert 'health_score' in data['diagnostic_report']

# Performance Testing
class PerformanceTestSuite:
    
    def __init__(self, service_url: str):
        self.service_url = service_url
    
    def load_test(self, endpoint: str, concurrent_requests: int = 10, duration: int = 60):
        """Simple load test"""
        import concurrent.futures
        import time
        
        start_time = time.time()
        results = []
        
        def make_request():
            try:
                start = time.time()
                response = requests.get(f"{self.service_url}{endpoint}", timeout=5)
                end = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end - start
                }
            except Exception as e:
                return {'error': str(e)}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            while time.time() - start_time < duration:
                futures = []
                for _ in range(concurrent_requests):
                    future = executor.submit(make_request)
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures, timeout=10):
                    result = future.result()
                    results.append(result)
                
                time.sleep(0.1)  # Brief pause between batches
        
        # Analyze results
        successful_requests = [r for r in results if 'status_code' in r and r['status_code'] == 200]
        failed_requests = [r for r in results if 'error' in r or r.get('status_code') != 200]
        
        if successful_requests:
            avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
            max_response_time = max(r['response_time'] for r in successful_requests)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        return {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(results) if results else 0,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time
        }

# Test Runner
class TestRunner:
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
    
    def run_service_tests(self, test_class):
        """Run tests for a single service"""
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        results = {}
        for method_name in test_methods:
            try:
                test_instance.setup_method()
                method = getattr(test_instance, method_name)
                method()
                results[method_name] = {'status': 'PASSED'}
                print(f"✅ {method_name}")
            except Exception as e:
                results[method_name] = {'status': 'FAILED', 'error': str(e)}
                print(f"❌ {method_name}: {e}")
            finally:
                test_instance.teardown_method()
        
        return results
    
    def run_integration_tests(self, test_suite: IntegrationTestSuite):
        """Run integration test suite"""
        test_suite.setup_class()
        try:
            test_methods = [method for method in dir(test_suite) if method.startswith('test_')]
            results = {}
            
            for method_name in test_methods:
                try:
                    method = getattr(test_suite, method_name)
                    method()
                    results[method_name] = {'status': 'PASSED'}
                    print(f"✅ Integration: {method_name}")
                except Exception as e:
                    results[method_name] = {'status': 'FAILED', 'error': str(e)}
                    print(f"❌ Integration: {method_name}: {e}")
            
            return results
        finally:
            test_suite.teardown_class()

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python testing_framework.py [unit|integration|performance] [service_name]")
        sys.exit(1)
    
    test_type = sys.argv[1]
    runner = TestRunner()
    
    if test_type == "unit":
        if len(sys.argv) < 3:
            print("Service name required for unit tests")
            sys.exit(1)
        
        service_name = sys.argv[2]
        
        if service_name == "vin-decoder":
            results = runner.run_service_tests(VINDecoderServiceTest)
        elif service_name == "diagnostic":
            results = runner.run_service_tests(DiagnosticServiceTest)
        else:
            print(f"Unknown service: {service_name}")
            sys.exit(1)
        
        print(f"\n📋 Unit Test Results for {service_name}:")
        print(json.dumps(results, indent=2))
    
    elif test_type == "integration":
        test_suite = MotospectIntegrationTest()
        results = runner.run_integration_tests(test_suite)
        
        print(f"\n📋 Integration Test Results:")
        print(json.dumps(results, indent=2))
    
    elif test_type == "performance":
        if len(sys.argv) < 4:
            print("Usage: python testing_framework.py performance [service_url] [endpoint]")
            sys.exit(1)
        
        service_url = sys.argv[2]
        endpoint = sys.argv[3]
        
        perf_tester = PerformanceTestSuite(service_url)
        results = perf_tester.load_test(endpoint, concurrent_requests=10, duration=30)
        
        print(f"\n📊 Performance Test Results:")
        print(json.dumps(results, indent=2))
    
    else:
        print("Unknown test type. Use: unit, integration, or performance")
        sys.exit(1)
