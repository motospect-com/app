#!/usr/bin/env python3
"""
MOTOSPECT Microservices Manager
Orchestrates all microservices with proper startup order and health checking
"""
import sys
import os
from pathlib import Path
import time
import asyncio

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from service_manager import ServiceManager
from microservices_config import get_all_services, get_startup_order

class MotospectMicroservicesManager:
    def __init__(self):
        self.service_manager = ServiceManager()
        self.services_config = get_all_services()
        self.startup_order = get_startup_order()
        
    def register_all_services(self):
        """Register all microservices with the service manager"""
        print("📋 Registering MOTOSPECT microservices...")
        
        for service_name, config in self.services_config.items():
            try:
                self.service_manager.register_service(config)
                print(f"✅ Registered {service_name}")
            except Exception as e:
                print(f"❌ Failed to register {service_name}: {e}")
    
    def start_all_services(self):
        """Start all services in dependency order"""
        print("🚀 Starting MOTOSPECT microservices ecosystem...")
        
        failed_services = []
        
        for service_name in self.startup_order:
            print(f"\n🔄 Starting {service_name}...")
            
            success = self.service_manager.start_service(service_name)
            if success:
                print(f"✅ {service_name} started successfully")
                # Wait a bit for service to fully initialize
                time.sleep(2)
            else:
                print(f"❌ Failed to start {service_name}")
                failed_services.append(service_name)
        
        if failed_services:
            print(f"\n⚠️  Failed to start: {', '.join(failed_services)}")
        else:
            print("\n🎉 All MOTOSPECT microservices started successfully!")
            self.print_service_urls()
    
    def stop_all_services(self):
        """Stop all services in reverse order"""
        print("🛑 Stopping MOTOSPECT microservices...")
        
        # Stop in reverse order to respect dependencies
        for service_name in reversed(self.startup_order):
            print(f"🔄 Stopping {service_name}...")
            self.service_manager.stop_service(service_name)
    
    def restart_all_services(self):
        """Restart all services"""
        print("🔄 Restarting MOTOSPECT microservices...")
        self.stop_all_services()
        time.sleep(3)
        self.start_all_services()
    
    def get_system_status(self):
        """Get status of all services"""
        print("\n📊 MOTOSPECT Microservices Status:")
        print("=" * 60)
        
        all_services = self.service_manager.list_all_services()
        
        healthy_count = 0
        total_count = len(all_services)
        
        for service in all_services:
            status_emoji = "✅" if service.get("healthy") else "❌" if service["status"] == "running" else "🛑"
            health_text = "Healthy" if service.get("healthy") else "Unhealthy" if service["status"] == "running" else "Stopped"
            
            print(f"{status_emoji} {service['name']:25} {service['status']:10} Port: {service.get('port', 'N/A'):5} {health_text}")
            
            if service.get("healthy"):
                healthy_count += 1
        
        print("=" * 60)
        print(f"📈 System Health: {healthy_count}/{total_count} services healthy")
        
        return all_services
    
    def print_service_urls(self):
        """Print accessible service URLs"""
        print("\n🔗 Service URLs:")
        print("-" * 40)
        
        all_services = self.service_manager.list_all_services()
        
        for service in all_services:
            if service.get("port") and service["status"] == "running":
                url = f"http://localhost:{service['port']}"
                print(f"  {service['name']:25} {url}")
        
        print("-" * 40)
        print("🌐 Main Entry Points:")
        print("  API Gateway:               http://localhost:8000")
        print("  API Documentation:         http://localhost:8000/docs")
    
    def health_check_all(self):
        """Perform health check on all services"""
        print("🏥 Performing health check on all services...")
        
        all_services = self.service_manager.list_all_services()
        results = {}
        
        for service in all_services:
            service_name = service['name']
            is_healthy = self.service_manager.is_service_healthy(service_name)
            results[service_name] = is_healthy
            
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"  {service_name:25} {status}")
        
        return results
    
    def install_dependencies(self):
        """Install dependencies for all microservices"""
        print("📦 Installing dependencies for all microservices...")
        
        services_path = Path(__file__).parent.parent / "services"
        
        for service_name in self.services_config.keys():
            service_path = services_path / service_name
            requirements_file = service_path / "requirements.txt"
            
            if requirements_file.exists():
                print(f"📦 Installing dependencies for {service_name}...")
                os.system(f"cd {service_path} && pip install -r requirements.txt")
            else:
                print(f"⚠️  No requirements.txt found for {service_name}")

def main():
    """Main CLI interface"""
    import sys
    
    manager = MotospectMicroservicesManager()
    
    if len(sys.argv) < 2:
        print("MOTOSPECT Microservices Manager")
        print("Usage: python microservices_manager.py [command]")
        print("\nCommands:")
        print("  register    - Register all services")
        print("  start       - Start all services")
        print("  stop        - Stop all services") 
        print("  restart     - Restart all services")
        print("  status      - Show service status")
        print("  health      - Perform health check")
        print("  install     - Install dependencies")
        print("  setup       - Full setup (register + install + start)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register":
        manager.register_all_services()
    elif command == "start":
        manager.register_all_services()
        manager.start_all_services()
    elif command == "stop":
        manager.stop_all_services()
    elif command == "restart":
        manager.restart_all_services()
    elif command == "status":
        manager.get_system_status()
    elif command == "health":
        manager.health_check_all()
    elif command == "install":
        manager.install_dependencies()
    elif command == "setup":
        print("🔧 Setting up MOTOSPECT microservices ecosystem...")
        manager.install_dependencies()
        manager.register_all_services()
        manager.start_all_services()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
