#!/usr/bin/env python3
"""Quick start script for MOTOSPECT services"""

import subprocess
import sys
import os
import time
import threading

def install_package(package):
    """Install a Python package"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])

def ensure_dependencies():
    """Ensure all required dependencies are installed"""
    print("Checking dependencies...")
    required = [
        "fastapi",
        "uvicorn[standard]",
        "aiohttp",
        "paho-mqtt",
        "python-dotenv",
        "python-multipart",
        "websockets",
        "starlette",
        "pandas",
        "numpy"
    ]
    
    for pkg in required:
        try:
            if pkg == "uvicorn[standard]":
                __import__("uvicorn")
            else:
                __import__(pkg.replace("-", "_"))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  Installing {pkg}...")
            try:
                install_package(pkg)
                print(f"  ✓ {pkg} installed")
            except Exception as e:
                print(f"  ✗ Failed to install {pkg}: {e}")

def start_backend():
    """Start the backend service"""
    print("\nStarting Backend on port 8030...")
    os.chdir("backend")
    subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8030",
        "--reload"
    ])
    os.chdir("..")
    time.sleep(5)

def start_frontend():
    """Start the frontend service"""
    print("\nStarting Frontend on port 3030...")
    os.chdir("frontend")
    
    # Check if node_modules exists
    if not os.path.exists("node_modules"):
        print("  Installing frontend dependencies...")
        subprocess.run(["npm", "install"], check=False)
    
    # Start the frontend
    env = os.environ.copy()
    env["PORT"] = "3030"
    subprocess.Popen(["npm", "start"], env=env)
    os.chdir("..")

def test_services():
    """Test that services are running"""
    import requests
    time.sleep(10)
    
    print("\nTesting services...")
    
    # Test backend
    try:
        response = requests.get("http://localhost:8030/health")
        if response.status_code == 200:
            print("  ✓ Backend is running on port 8030")
        else:
            print(f"  ✗ Backend returned status {response.status_code}")
    except Exception as e:
        print(f"  ✗ Backend not responding: {e}")
    
    # Test frontend
    try:
        response = requests.get("http://localhost:3030")
        print("  ✓ Frontend is accessible on port 3030")
    except Exception as e:
        print(f"  ✗ Frontend not responding: {e}")

def main():
    print("=" * 60)
    print("MOTOSPECT Quick Start")
    print("=" * 60)
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("Creating .env from .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src:
                with open(".env", "w") as dst:
                    dst.write(src.read())
    
    # Ensure dependencies
    ensure_dependencies()
    
    # Start services
    start_backend()
    start_frontend()
    
    # Test services
    test_services()
    
    print("\n" + "=" * 60)
    print("Services Started!")
    print("=" * 60)
    print("Backend API: http://localhost:8030")
    print("API Docs: http://localhost:8030/docs")
    print("Frontend: http://localhost:3030")
    print("Customer Portal: http://localhost:3040")
    print("\nPress Ctrl+C to stop all services")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        subprocess.run(["pkill", "-f", "npm"], check=False)
        print("Services stopped.")

if __name__ == "__main__":
    main()
