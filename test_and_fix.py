#!/usr/bin/env python3
"""Test and fix service startup issues"""

import subprocess
import sys
import os
import time

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("MOTOSPECT Service Diagnostic and Startup")
    print("=" * 50)
    
    # Check Python
    print("\n1. Checking Python...")
    stdout, stderr, code = run_cmd("python3 --version")
    print(f"   Python: {stdout.strip() if stdout else 'Not found'}")
    
    # Check Docker
    print("\n2. Checking Docker...")
    stdout, stderr, code = run_cmd("docker --version")
    print(f"   Docker: {stdout.strip() if stdout else 'Not available'}")
    
    stdout, stderr, code = run_cmd("systemctl is-active docker")
    print(f"   Docker status: {stdout.strip() if stdout else 'inactive'}")
    
    # Try Docker approach
    print("\n3. Attempting Docker startup...")
    if stdout.strip() == "active":
        print("   Starting services with Docker...")
        run_cmd("docker-compose down 2>/dev/null")
        stdout, stderr, code = run_cmd("docker-compose up -d backend frontend mosquitto 2>&1")
        if code == 0:
            print("   Docker services started")
            time.sleep(5)
            # Test backend
            stdout, stderr, code = run_cmd("curl -s http://localhost:8030/health")
            if stdout:
                print("   ✓ Backend is running on port 8030")
            else:
                print("   ✗ Backend not responding")
        else:
            print(f"   Docker failed: {stderr}")
    
    # Check services
    print("\n4. Service Status:")
    services = [
        ("Backend", "http://localhost:8030/health"),
        ("Frontend", "http://localhost:3030"),
        ("Customer Portal", "http://localhost:3040")
    ]
    
    for name, url in services:
        stdout, stderr, code = run_cmd(f"curl -s -o /dev/null -w '%{{http_code}}' {url}")
        if stdout and stdout.strip() != "000":
            print(f"   ✓ {name}: Running (HTTP {stdout.strip()})")
        else:
            print(f"   ✗ {name}: Not responding")
    
    # Try manual Python startup if services aren't running
    stdout, stderr, code = run_cmd("curl -s http://localhost:8030/health")
    if not stdout:
        print("\n5. Attempting manual startup...")
        print("   Creating virtual environment...")
        os.system("python3 -m venv /tmp/motospect_venv 2>/dev/null")
        
        print("   Installing dependencies...")
        os.system("/tmp/motospect_venv/bin/pip install -q fastapi uvicorn aiohttp paho-mqtt python-dotenv 2>/dev/null")
        
        print("   Starting backend...")
        os.system("cd backend && /tmp/motospect_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8030 &")
        time.sleep(5)
        
        stdout, stderr, code = run_cmd("curl -s http://localhost:8030/health")
        if stdout:
            print("   ✓ Backend started successfully")
        else:
            print("   ✗ Backend startup failed")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    stdout, stderr, code = run_cmd("curl -s http://localhost:8030/health")
    if stdout:
        print("✓ Backend API is running at http://localhost:8030")
        print("✓ API Docs available at http://localhost:8030/docs")
    else:
        print("✗ Backend is not running")
        print("  Try: docker-compose up -d")
        print("  Or: cd backend && python3 -m uvicorn main:app --port 8030")
    
    stdout, stderr, code = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost:3030")
    if stdout and stdout.strip() != "000":
        print("✓ Frontend is running at http://localhost:3030")
    else:
        print("✗ Frontend is not running")
        print("  Try: cd frontend && npm install && PORT=3030 npm start")

if __name__ == "__main__":
    main()
