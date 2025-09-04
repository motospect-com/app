#!/usr/bin/env python3
"""
Pre-flight checks for MOTOSPECT system
Validates all services, dependencies, and configurations before deployment or runtime
"""
import os
import sys
import json
import subprocess
import asyncio
import aiohttp
import socket
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import psutil
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreflightChecker:
    """Comprehensive pre-flight validation for MOTOSPECT"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "passed": [],
            "failed": [],
            "warnings": [],
            "errors": [],
            "system_info": {}
        }
        self.docker_client = None
        
    def log(self, level: str, message: str):
        """Log message with appropriate level"""
        if level == "info":
            logger.info(f"✓ {message}")
            self.results["passed"].append(message)
        elif level == "warning":
            logger.warning(f"⚠ {message}")
            self.results["warnings"].append(message)
        elif level == "error":
            logger.error(f"✗ {message}")
            self.results["failed"].append(message)
        elif level == "debug" and self.verbose:
            logger.debug(f"  {message}")
    
    # --- System Checks ---
    
    def check_system_resources(self) -> bool:
        """Check if system has adequate resources"""
        try:
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > 90:
                self.log("warning", f"High CPU usage: {cpu_percent}%")
            else:
                self.log("info", f"CPU resources adequate: {cpu_percent}% used, {cpu_count} cores")
            
            # Check Memory
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_percent = memory.percent
            
            if memory_gb < 2:
                self.log("error", f"Insufficient memory: {memory_gb:.1f}GB (minimum 2GB required)")
                return False
            elif memory_percent > 90:
                self.log("warning", f"High memory usage: {memory_percent}%")
            else:
                self.log("info", f"Memory adequate: {memory_gb:.1f}GB total, {memory_percent}% used")
            
            # Check Disk Space
            disk = psutil.disk_usage('/')
            disk_gb_free = disk.free / (1024**3)
            disk_percent = disk.percent
            
            if disk_gb_free < 5:
                self.log("error", f"Insufficient disk space: {disk_gb_free:.1f}GB free (minimum 5GB required)")
                return False
            else:
                self.log("info", f"Disk space adequate: {disk_gb_free:.1f}GB free, {disk_percent}% used")
            
            # Store system info
            self.results["system_info"] = {
                "cpu_cores": cpu_count,
                "cpu_percent": cpu_percent,
                "memory_gb": memory_gb,
                "memory_percent": memory_percent,
                "disk_gb_free": disk_gb_free,
                "disk_percent": disk_percent
            }
            
            return True
            
        except Exception as e:
            self.log("error", f"Failed to check system resources: {e}")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        try:
            import sys
            version = sys.version_info
            
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                self.log("error", f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
                return False
            else:
                self.log("info", f"Python version OK: {version.major}.{version.minor}.{version.micro}")
                return True
                
        except Exception as e:
            self.log("error", f"Failed to check Python version: {e}")
            return False
    
    def check_required_ports(self) -> bool:
        """Check if required ports are available"""
        required_ports = {
            3030: "Frontend",
            3040: "Customer Portal", 
            3050: "Report Service",
            8030: "Backend API",
            1883: "MQTT Broker",
            9002: "MQTT WebSocket"
        }
        
        all_available = True
        
        for port, service in required_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    self.log("debug", f"Port {port} ({service}) is in use")
                else:
                    self.log("debug", f"Port {port} ({service}) is available")
            except Exception as e:
                self.log("warning", f"Could not check port {port}: {e}")
            finally:
                sock.close()
        
        return all_available
    
    # --- Dependency Checks ---
    
    def check_python_dependencies(self) -> bool:
        """Check if all Python dependencies are installed"""
        try:
            requirements_files = [
                "backend/requirements.txt",
                "requirements-automation.txt"
            ]
            
            for req_file in requirements_files:
                if os.path.exists(req_file):
                    self.log("debug", f"Checking {req_file}")
                    
                    with open(req_file, 'r') as f:
                        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    
                    missing = []
                    for req in requirements:
                        package_name = req.split('==')[0].split('>=')[0].split('<')[0].strip()
                        try:
                            __import__(package_name.replace('-', '_'))
                        except ImportError:
                            missing.append(package_name)
                    
                    if missing:
                        self.log("error", f"Missing Python packages: {', '.join(missing)}")
                        self.log("debug", f"Install with: pip install {' '.join(missing)}")
                        return False
                    else:
                        self.log("info", f"All Python dependencies from {req_file} are installed")
            
            return True
            
        except Exception as e:
            self.log("error", f"Failed to check Python dependencies: {e}")
            return False
    
    def check_node_dependencies(self) -> bool:
        """Check if Node.js and npm dependencies are installed"""
        try:
            # Check Node.js
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("error", "Node.js not found")
                return False
            else:
                node_version = result.stdout.strip()
                self.log("info", f"Node.js found: {node_version}")
            
            # Check npm
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("error", "npm not found")
                return False
            else:
                npm_version = result.stdout.strip()
                self.log("info", f"npm found: {npm_version}")
            
            # Check package.json files
            package_dirs = [
                "frontend",
                "customer-portal",
                "report-service"
            ]
            
            for dir_name in package_dirs:
                package_file = f"{dir_name}/package.json"
                if os.path.exists(package_file):
                    node_modules = f"{dir_name}/node_modules"
                    if not os.path.exists(node_modules):
                        self.log("warning", f"Node modules not installed in {dir_name}")
                        self.log("debug", f"Run: cd {dir_name} && npm install")
                    else:
                        self.log("info", f"Node modules installed in {dir_name}")
            
            return True
            
        except FileNotFoundError:
            self.log("error", "Node.js or npm not found in PATH")
            return False
        except Exception as e:
            self.log("error", f"Failed to check Node dependencies: {e}")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            # Check Docker CLI
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("error", "Docker not found")
                return False
            else:
                docker_version = result.stdout.strip()
                self.log("info", f"Docker found: {docker_version}")
            
            # Check Docker daemon
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.log("info", "Docker daemon is running")
            
            # Check Docker Compose
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                compose_version = result.stdout.strip()
                self.log("info", f"Docker Compose found: {compose_version}")
            else:
                self.log("warning", "Docker Compose not found (optional)")
            
            return True
            
        except docker.errors.DockerException:
            self.log("error", "Docker daemon is not running")
            return False
        except FileNotFoundError:
            self.log("error", "Docker not found in PATH")
            return False
        except Exception as e:
            self.log("error", f"Failed to check Docker: {e}")
            return False
    
    # --- Configuration Checks ---
    
    def check_env_files(self) -> bool:
        """Check if environment files are configured"""
        try:
            env_file = ".env"
            env_example = ".env.example"
            
            if not os.path.exists(env_file):
                if os.path.exists(env_example):
                    self.log("warning", f".env file not found, copy from {env_example}")
                    self.log("debug", f"Run: cp {env_example} {env_file}")
                else:
                    self.log("error", "No .env or .env.example file found")
                return False
            else:
                self.log("info", ".env file exists")
                
                # Check required variables
                required_vars = [
                    "BACKEND_URL",
                    "FRONTEND_URL",
                    "MQTT_BROKER_HOST"
                ]
                
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    missing_vars = []
                    for var in required_vars:
                        if var not in env_content:
                            missing_vars.append(var)
                    
                    if missing_vars:
                        self.log("warning", f"Missing environment variables: {', '.join(missing_vars)}")
                    else:
                        self.log("info", "All required environment variables are set")
            
            return True
            
        except Exception as e:
            self.log("error", f"Failed to check environment files: {e}")
            return False
    
    def check_file_structure(self) -> bool:
        """Check if required files and directories exist"""
        try:
            required_paths = {
                "backend/": "Backend directory",
                "frontend/": "Frontend directory",
                "customer-portal/": "Customer Portal directory",
                "backend/main.py": "Backend main file",
                "backend/motospect_core.py": "Core module",
                "backend/sensor_modules.py": "Sensor modules",
                "backend/logging_config.py": "Logging configuration",
                "docker-compose.yml": "Docker Compose file",
                "Makefile": "Makefile"
            }
            
            missing_paths = []
            
            for path, description in required_paths.items():
                if not os.path.exists(path):
                    missing_paths.append(f"{path} ({description})")
                    self.log("debug", f"Missing: {path}")
                else:
                    self.log("debug", f"Found: {path}")
            
            if missing_paths:
                self.log("error", f"Missing required files/directories: {len(missing_paths)}")
                for path in missing_paths[:5]:  # Show first 5
                    self.log("debug", f"  - {path}")
                return False
            else:
                self.log("info", "All required files and directories present")
                return True
                
        except Exception as e:
            self.log("error", f"Failed to check file structure: {e}")
            return False
    
    # --- Service Checks ---
    
    async def check_backend_health(self) -> bool:
        """Check if backend service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8030/health"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "healthy":
                            self.log("info", "Backend service is healthy")
                            return True
                        else:
                            self.log("error", f"Backend unhealthy: {data}")
                            return False
                    else:
                        self.log("error", f"Backend returned status {response.status}")
                        return False
                        
        except aiohttp.ClientConnectionError:
            self.log("warning", "Backend service not running (run 'make up' to start)")
            return False
        except Exception as e:
            self.log("error", f"Failed to check backend health: {e}")
            return False
    
    async def check_frontend_health(self) -> bool:
        """Check if frontend service is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:3030"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        self.log("info", "Frontend service is accessible")
                        return True
                    else:
                        self.log("error", f"Frontend returned status {response.status}")
                        return False
                        
        except aiohttp.ClientConnectionError:
            self.log("warning", "Frontend service not running")
            return False
        except Exception as e:
            self.log("error", f"Failed to check frontend: {e}")
            return False
    
    def check_docker_containers(self) -> bool:
        """Check status of Docker containers"""
        try:
            if not self.docker_client:
                self.docker_client = docker.from_env()
            
            expected_containers = [
                "motospect-backend",
                "motospect-frontend",
                "motospect-customer-portal",
                "motospect-mosquitto"
            ]
            
            running_containers = []
            for container in self.docker_client.containers.list():
                running_containers.append(container.name)
            
            for expected in expected_containers:
                if expected in running_containers:
                    self.log("debug", f"Container {expected} is running")
                else:
                    self.log("debug", f"Container {expected} is not running")
            
            if running_containers:
                self.log("info", f"Docker containers running: {len(running_containers)}")
            else:
                self.log("warning", "No Docker containers running")
            
            return True
            
        except Exception as e:
            self.log("debug", f"Could not check Docker containers: {e}")
            return True  # Not critical
    
    # --- Security Checks ---
    
    def check_security(self) -> bool:
        """Basic security checks"""
        try:
            # Check for hardcoded credentials
            sensitive_files = [
                "backend/main.py",
                "backend/config.py",
                ".env"
            ]
            
            sensitive_patterns = [
                "password=",
                "api_key=",
                "secret=",
                "token="
            ]
            
            issues_found = False
            
            for file_path in sensitive_files:
                if os.path.exists(file_path) and file_path != ".env":
                    with open(file_path, 'r') as f:
                        content = f.read().lower()
                        for pattern in sensitive_patterns:
                            if pattern in content and '=' in content:
                                # Check if it's not an environment variable
                                if 'os.getenv' not in content and 'environ' not in content:
                                    self.log("warning", f"Possible hardcoded credential in {file_path}")
                                    issues_found = True
                                    break
            
            if not issues_found:
                self.log("info", "No obvious hardcoded credentials found")
            
            # Check file permissions
            if os.path.exists(".env"):
                stat_info = os.stat(".env")
                mode = oct(stat_info.st_mode)[-3:]
                if mode != "600" and mode != "644":
                    self.log("warning", f".env file permissions too open: {mode}")
            
            return True
            
        except Exception as e:
            self.log("error", f"Failed to perform security checks: {e}")
            return False
    
    # --- Main Runner ---
    
    async def run_all_checks(self) -> bool:
        """Run all pre-flight checks"""
        logger.info("="*60)
        logger.info("MOTOSPECT PRE-FLIGHT CHECKS")
        logger.info("="*60)
        
        all_passed = True
        
        # System checks
        logger.info("\n[System Checks]")
        all_passed &= self.check_system_resources()
        all_passed &= self.check_python_version()
        self.check_required_ports()  # Non-critical
        
        # Dependency checks
        logger.info("\n[Dependency Checks]")
        all_passed &= self.check_python_dependencies()
        self.check_node_dependencies()  # Warning only
        self.check_docker()  # Warning only
        
        # Configuration checks
        logger.info("\n[Configuration Checks]")
        all_passed &= self.check_env_files()
        all_passed &= self.check_file_structure()
        
        # Service checks (if running)
        logger.info("\n[Service Checks]")
        await self.check_backend_health()
        await self.check_frontend_health()
        self.check_docker_containers()
        
        # Security checks
        logger.info("\n[Security Checks]")
        self.check_security()
        
        # Generate report
        self.generate_report()
        
        return all_passed and len(self.results["failed"]) == 0
    
    def generate_report(self):
        """Generate pre-flight check report"""
        logger.info("\n" + "="*60)
        logger.info("PRE-FLIGHT CHECK SUMMARY")
        logger.info("="*60)
        
        total_checks = len(self.results["passed"]) + len(self.results["failed"])
        
        logger.info(f"✓ Passed: {len(self.results['passed'])}")
        logger.info(f"✗ Failed: {len(self.results['failed'])}")
        logger.info(f"⚠ Warnings: {len(self.results['warnings'])}")
        logger.info(f"Total Checks: {total_checks}")
        
        if self.results["failed"]:
            logger.info("\nFailed Checks:")
            for item in self.results["failed"]:
                logger.error(f"  ✗ {item}")
        
        if self.results["warnings"]:
            logger.info("\nWarnings:")
            for item in self.results["warnings"]:
                logger.warning(f"  ⚠ {item}")
        
        # Save report
        report_file = f"preflight-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"\nDetailed report saved to: {report_file}")
        
        # Overall status
        if len(self.results["failed"]) == 0:
            logger.info("\n✅ PRE-FLIGHT CHECKS PASSED - System ready for deployment")
            return 0
        else:
            logger.error("\n❌ PRE-FLIGHT CHECKS FAILED - Please fix issues before deployment")
            return 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MOTOSPECT Pre-flight Checks")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues automatically")
    args = parser.parse_args()
    
    checker = PreflightChecker(verbose=args.verbose)
    
    # Run async checks
    loop = asyncio.get_event_loop()
    all_passed = loop.run_until_complete(checker.run_all_checks())
    
    # Auto-fix if requested
    if args.fix and not all_passed:
        logger.info("\n[Auto-fix Mode]")
        logger.info("Attempting to fix issues...")
        
        # Try to install missing Python packages
        if "Missing Python packages" in str(checker.results["failed"]):
            logger.info("Installing missing Python packages...")
            subprocess.run(["pip", "install", "-r", "backend/requirements.txt"])
        
        # Create .env from example
        if not os.path.exists(".env") and os.path.exists(".env.example"):
            logger.info("Creating .env from .env.example...")
            subprocess.run(["cp", ".env.example", ".env"])
        
        logger.info("Auto-fix complete. Please run checks again.")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
