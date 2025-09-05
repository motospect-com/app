#!/usr/bin/env python3
"""Diagnose MOTOSPECT system issues"""

import os
import sys
import subprocess
import json

def check_command(cmd, name):
    """Check if a command exists"""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        print(f"✓ {name} found")
        return True
    except:
        print(f"✗ {name} not found")
        return False

def check_python_module(module):
    """Check if Python module is installed"""
    try:
        __import__(module)
        print(f"  ✓ {module}")
        return True
    except ImportError:
        print(f"  ✗ {module} - NOT INSTALLED")
        return False

def check_port(port):
    """Check if port is in use"""
    try:
        result = subprocess.run(
            f"lsof -i :{port} 2>/dev/null | grep LISTEN",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"  Port {port}: IN USE")
            return True
        else:
            print(f"  Port {port}: FREE")
            return False
    except:
        return False

print("=" * 60)
print("MOTOSPECT System Diagnostics")
print("=" * 60)

# Check system dependencies
print("\n1. System Dependencies:")
check_command("docker", "Docker")
check_command("docker-compose", "Docker Compose")
check_command("node", "Node.js")
check_command("npm", "NPM")
check_command("python3", "Python 3")

# Check Python modules
print("\n2. Python Modules:")
modules = [
    "fastapi",
    "uvicorn",
    "aiohttp",
    "paho.mqtt",
    "dotenv",
    "starlette",
    "websockets"
]
all_modules = True
for mod in modules:
    if not check_python_module(mod.replace("-", "_").replace(".", "")):
        all_modules = False

# Check ports
print("\n3. Port Status:")
ports = {
    8030: "Backend",
    3030: "Frontend",
    3040: "Customer Portal",
    1884: "MQTT"
}
for port, service in ports.items():
    print(f"  {service}:")
    check_port(port)

# Check Docker status
print("\n4. Docker Status:")
try:
    result = subprocess.run(
        ["docker", "ps", "--format", "json"],
        capture_output=True,
        text=True
    )
    if result.stdout:
        containers = result.stdout.strip().split('\n')
        print(f"  Running containers: {len(containers)}")
        for container in containers:
            try:
                data = json.loads(container)
                print(f"    - {data.get('Names', 'Unknown')}: {data.get('Status', 'Unknown')}")
            except:
                pass
    else:
        print("  No containers running")
except Exception as e:
    print(f"  Docker check failed: {e}")

# Check environment
print("\n5. Environment:")
if os.path.exists(".env"):
    print("  ✓ .env file exists")
    with open(".env", "r") as f:
        lines = f.readlines()
        backend_port = None
        frontend_port = None
        for line in lines:
            if "BACKEND_PORT" in line:
                backend_port = line.strip()
            if "FRONTEND_PORT" in line:
                frontend_port = line.strip()
        if backend_port:
            print(f"  {backend_port}")
        if frontend_port:
            print(f"  {frontend_port}")
else:
    print("  ✗ .env file missing")

# Recommendations
print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)

if not all_modules:
    print("\n1. Install missing Python modules:")
    print("   pip3 install --user fastapi uvicorn[standard] aiohttp paho-mqtt python-dotenv")

print("\n2. Quick fix commands:")
print("   # Clean restart")
print("   make clean && make build && make up")
print("")
print("   # Check status")
print("   make status")
print("")
print("   # Run tests")
print("   make test-complete")

print("\n3. Manual startup (if Docker fails):")
print("   # Terminal 1 - Backend")
print("   cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8030")
print("")
print("   # Terminal 2 - Frontend")
print("   cd frontend && PORT=3030 npm start")

print("\n" + "=" * 60)
