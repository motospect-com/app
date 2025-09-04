#!/usr/bin/env python3
"""Test and fix MOTOSPECT startup issues"""

import subprocess
import time
import requests
import sys

def test_backend_import():
    """Test if backend can be imported"""
    print("Testing backend imports...")
    try:
        # Try importing backend modules
        import sys
        sys.path.insert(0, './backend')
        
        # Test basic imports
        try:
            import fastapi
            print("  ✓ FastAPI installed")
        except ImportError:
            print("  ✗ FastAPI not installed - installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "fastapi"], check=False)
            
        try:
            import uvicorn
            print("  ✓ Uvicorn installed")
        except ImportError:
            print("  ✗ Uvicorn not installed - installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "uvicorn[standard]"], check=False)
            
        # Try importing main app
        from main import app
        print("  ✓ Backend main.py loads successfully")
        return True
    except Exception as e:
        print(f"  ✗ Backend import failed: {e}")
        return False

def start_backend():
    """Start backend service"""
    print("\nStarting backend service...")
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]
    process = subprocess.Popen(cmd, cwd="./backend")
    time.sleep(5)  # Wait for startup
    
    # Test if backend is running
    try:
        response = requests.get("http://localhost:8030/health", timeout=5)
        if response.status_code == 200:
            print("  ✓ Backend is running on port 8030")
            return process
        else:
            print(f"  ✗ Backend returned status {response.status_code}")
            process.terminate()
            return None
    except Exception as e:
        print(f"  ✗ Backend not responding: {e}")
        process.terminate()
        return None

def test_frontend():
    """Test frontend availability"""
    print("\nChecking frontend...")
    try:
        response = requests.get("http://localhost:3030", timeout=5)
        if response.status_code == 200:
            print("  ✓ Frontend is running on port 3030")
            return True
    except:
        print("  ✗ Frontend not responding on port 3030")
    return False

def main():
    print("=" * 60)
    print("MOTOSPECT Startup Test")
    print("=" * 60)
    
    # Test backend
    if test_backend_import():
        backend_process = start_backend()
        if backend_process:
            print("\n✓ Backend started successfully")
            
            # Test API endpoints
            print("\nTesting API endpoints...")
            test_endpoints = [
                ("/", "Root"),
                ("/health", "Health"),
                ("/api/vin/validate/1HGBH41JXMN109186", "VIN Validation"),
            ]
            
            for endpoint, name in test_endpoints:
                try:
                    response = requests.get(f"http://localhost:8030{endpoint}", timeout=5)
                    print(f"  {name}: {response.status_code}")
                except Exception as e:
                    print(f"  {name}: Failed - {e}")
            
            # Keep running for manual testing
            print("\n" + "=" * 60)
            print("Backend is running. Press Ctrl+C to stop.")
            print("Access points:")
            print("  API: http://localhost:8030")
            print("  Docs: http://localhost:8030/docs")
            print("=" * 60)
            
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\nStopping backend...")
                backend_process.terminate()
    else:
        print("\n✗ Cannot start backend - import issues need to be fixed")
        
        # Try to install missing dependencies
        print("\nAttempting to install dependencies...")
        deps = ["fastapi", "uvicorn[standard]", "aiohttp", "paho-mqtt", "python-dotenv", "python-multipart", "starlette"]
        for dep in deps:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", dep], check=False)
        
        print("\nDependencies installed. Please run this script again.")

if __name__ == "__main__":
    main()
