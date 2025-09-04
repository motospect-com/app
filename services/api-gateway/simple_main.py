#!/usr/bin/env python3
"""
Simple API Gateway - Working Version
"""
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="MOTOSPECT API Gateway",
    description="API Gateway for MOTOSPECT microservices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "vin-decoder": "http://localhost:8001",
    "fault-detector": "http://localhost:8002", 
    "diagnostic": "http://localhost:8003",
    "mqtt-bridge": "http://localhost:8004"
}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "API Gateway",
        "version": "1.0.0",
        "port": int(os.getenv("PORT", "8000"))
    }

@app.get("/")
def service_info():
    return {
        "service": "MOTOSPECT API Gateway",
        "version": "1.0.0",
        "description": "Central entry point for all MOTOSPECT services",
        "services": SERVICES,
        "endpoints": {
            "vin": "/api/vin/*",
            "fault": "/api/fault/*", 
            "diagnostic": "/api/diagnostic/*",
            "mqtt": "/api/mqtt/*"
        },
        "port": int(os.getenv("PORT", "8000"))
    }

@app.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    status = {}
    
    for service_name, url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{url}/health")
                status[service_name] = {
                    "url": url,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                }
        except Exception as e:
            status[service_name] = {
                "url": url,
                "status": "unreachable",
                "error": str(e)
            }
    
    return status

# VIN Service Proxy
@app.get("/api/vin/decode/{vin}")
async def decode_vin(vin: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICES['vin-decoder']}/api/vin/decode/{vin}")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"VIN service unavailable: {str(e)}")

@app.get("/api/vin/validate/{vin}")
async def validate_vin(vin: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICES['vin-decoder']}/api/vin/validate/{vin}")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"VIN service unavailable: {str(e)}")

# Fault Detector Proxy
@app.post("/api/fault/analyze")
async def analyze_faults(data: dict = {}):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{SERVICES['fault-detector']}/api/fault/analyze", json=data)
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Fault detector service unavailable: {str(e)}")

# Diagnostic Service Proxy  
@app.post("/api/diagnostic/report")
async def generate_report(data: dict = {}):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{SERVICES['diagnostic']}/api/diagnostic/report", json=data)
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Diagnostic service unavailable: {str(e)}")

# MQTT Bridge Proxy
@app.get("/api/mqtt/status")
async def mqtt_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICES['mqtt-bridge']}/api/mqtt/status")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MQTT service unavailable: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting API Gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
