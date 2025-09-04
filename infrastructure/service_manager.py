#!/usr/bin/env python3
"""
Service Manager - Dynamiczne zarządzanie portami i serwisami
Rozwiązuje problemy z konfliktami portów i uruchamianiem serwisów
"""
import json
import socket
import subprocess
import time
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class ServiceConfig:
    name: str
    command: List[str]
    working_dir: str
    port: Optional[int] = None
    health_endpoint: str = "/health"
    environment: Dict[str, str] = None
    dependencies: List[str] = None

@dataclass
class ServiceInfo:
    config: ServiceConfig
    status: ServiceStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    started_at: Optional[float] = None
    health_url: Optional[str] = None

class PortManager:
    def __init__(self, start_port: int = 8000, end_port: int = 9000):
        self.start_port = start_port
        self.end_port = end_port
        self.allocated_ports: Dict[str, int] = {}
        self.reserved_ports = {8030, 3030, 3040, 3050}  # Existing services
    
    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    def allocate_port(self, service_name: str) -> int:
        """Allocate next available port for service"""
        if service_name in self.allocated_ports:
            port = self.allocated_ports[service_name]
            if self.is_port_available(port):
                return port
        
        for port in range(self.start_port, self.end_port):
            if port in self.reserved_ports:
                continue
            if port in self.allocated_ports.values():
                continue
            if self.is_port_available(port):
                self.allocated_ports[service_name] = port
                return port
        
        raise RuntimeError(f"No available ports for service {service_name}")
    
    def free_port(self, service_name: str):
        """Free port allocated to service"""
        if service_name in self.allocated_ports:
            del self.allocated_ports[service_name]
    
    def get_port(self, service_name: str) -> Optional[int]:
        """Get port allocated to service"""
        return self.allocated_ports.get(service_name)

class ServiceRegistry:
    def __init__(self, registry_file: str = "service_registry.json"):
        self.registry_file = Path(registry_file)
        self.services: Dict[str, ServiceInfo] = {}
        self.load_registry()
    
    def load_registry(self):
        """Load service registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for name, service_data in data.items():
                        config = ServiceConfig(**service_data['config'])
                        info = ServiceInfo(
                            config=config,
                            status=ServiceStatus(service_data.get('status', 'stopped')),
                            port=service_data.get('port'),
                            pid=service_data.get('pid')
                        )
                        self.services[name] = info
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")
    
    def save_registry(self):
        """Save service registry to file"""
        data = {}
        for name, info in self.services.items():
            data[name] = {
                'config': asdict(info.config),
                'status': info.status.value,
                'port': info.port,
                'pid': info.pid,
                'started_at': info.started_at
            }
        
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_service(self, service_info: ServiceInfo):
        """Register service in registry"""
        self.services[service_info.config.name] = service_info
        self.save_registry()
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get service info by name"""
        return self.services.get(name)
    
    def list_services(self) -> List[ServiceInfo]:
        """List all registered services"""
        return list(self.services.values())

class ServiceManager:
    def __init__(self):
        self.port_manager = PortManager()
        self.registry = ServiceRegistry()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.health_checker = HealthChecker()
    
    def register_service(self, config: ServiceConfig) -> ServiceInfo:
        """Register new service"""
        if not config.port:
            config.port = self.port_manager.allocate_port(config.name)
        
        service_info = ServiceInfo(
            config=config,
            status=ServiceStatus.STOPPED,
            port=config.port,
            health_url=f"http://localhost:{config.port}{config.health_endpoint}"
        )
        
        self.registry.register_service(service_info)
        return service_info
    
    def start_service(self, service_name: str) -> bool:
        """Start service by name"""
        service_info = self.registry.get_service(service_name)
        if not service_info:
            print(f"Service {service_name} not found")
            return False
        
        if service_info.status == ServiceStatus.RUNNING:
            print(f"Service {service_name} already running on port {service_info.port}")
            return True
        
        # Check dependencies
        if service_info.config.dependencies:
            for dep in service_info.config.dependencies:
                if not self.is_service_healthy(dep):
                    print(f"Dependency {dep} not available for {service_name}")
                    return False
        
        # Start service
        env = service_info.config.environment or {}
        env['PORT'] = str(service_info.port)
        
        try:
            service_info.status = ServiceStatus.STARTING
            service_info.started_at = time.time()
            
            import os
            process = subprocess.Popen(
                service_info.config.command,
                cwd=service_info.config.working_dir,
                env={**os.environ, **env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            service_info.pid = process.pid
            self.processes[service_name] = process
            
            # Wait for service to be healthy
            if self.wait_for_health(service_name, timeout=30):
                service_info.status = ServiceStatus.RUNNING
                print(f"✅ Service {service_name} started on port {service_info.port}")
                self.registry.save_registry()
                return True
            else:
                service_info.status = ServiceStatus.ERROR
                print(f"❌ Service {service_name} failed to start")
                return False
                
        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            print(f"❌ Error starting {service_name}: {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop service by name"""
        service_info = self.registry.get_service(service_name)
        if not service_info:
            return False
        
        if service_name in self.processes:
            process = self.processes[service_name]
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes[service_name]
        
        service_info.status = ServiceStatus.STOPPED
        service_info.pid = None
        self.port_manager.free_port(service_name)
        self.registry.save_registry()
        
        print(f"🛑 Service {service_name} stopped")
        return True
    
    def restart_service(self, service_name: str) -> bool:
        """Restart service"""
        self.stop_service(service_name)
        time.sleep(1)
        return self.start_service(service_name)
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy"""
        service_info = self.registry.get_service(service_name)
        if not service_info or not service_info.health_url:
            return False
        
        return self.health_checker.check_health(service_info.health_url)
    
    def wait_for_health(self, service_name: str, timeout: int = 30) -> bool:
        """Wait for service to become healthy"""
        service_info = self.registry.get_service(service_name)
        if not service_info:
            return False
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_service_healthy(service_name):
                return True
            time.sleep(1)
        return False
    
    def get_service_status(self, service_name: str) -> Dict:
        """Get detailed service status"""
        service_info = self.registry.get_service(service_name)
        if not service_info:
            return {"error": "Service not found"}
        
        return {
            "name": service_info.config.name,
            "status": service_info.status.value,
            "port": service_info.port,
            "pid": service_info.pid,
            "health_url": service_info.health_url,
            "healthy": self.is_service_healthy(service_name) if service_info.status == ServiceStatus.RUNNING else False
        }
    
    def list_all_services(self) -> List[Dict]:
        """List all services with status"""
        services = []
        for service_info in self.registry.list_services():
            status = self.get_service_status(service_info.config.name)
            services.append(status)
        return services

class HealthChecker:
    def check_health(self, health_url: str, timeout: int = 5) -> bool:
        """Check if service is healthy via HTTP"""
        try:
            response = requests.get(health_url, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

# CLI Interface
if __name__ == "__main__":
    import sys
    import os
    
    manager = ServiceManager()
    
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py [start|stop|restart|status|list] [service_name]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        services = manager.list_all_services()
        print("\n📋 MOTOSPECT Services:")
        print("-" * 60)
        for service in services:
            status_emoji = "✅" if service.get("healthy") else "❌" if service["status"] == "running" else "🛑"
            print(f"{status_emoji} {service['name']:20} {service['status']:10} Port: {service.get('port', 'N/A')}")
    
    elif len(sys.argv) < 3:
        print("Service name required")
        sys.exit(1)
    
    else:
        service_name = sys.argv[2]
        
        if command == "start":
            success = manager.start_service(service_name)
            sys.exit(0 if success else 1)
        elif command == "stop":
            manager.stop_service(service_name)
        elif command == "restart":
            manager.restart_service(service_name)
        elif command == "status":
            status = manager.get_service_status(service_name)
            print(json.dumps(status, indent=2))
