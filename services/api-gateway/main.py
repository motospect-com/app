#!/usr/bin/env python3
"""
API Gateway Microservice
Central entry point for all MOTOSPECT services with routing and load balancing
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import sys
import uvicorn
import httpx
import asyncio
from pathlib import Path
import json

app = FastAPI(
    title="MOTOSPECT API Gateway",
    description="Central API Gateway for MOTOSPECT microservices ecosystem",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add backend and infrastructure paths for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
infrastructure_path = Path(__file__).parent.parent.parent / "infrastructure"
sys.path.append(str(backend_path))
sys.path.append(str(infrastructure_path))

from config import config

# Service registry with health checking
SERVICE_REGISTRY = {
    "vin-decoder": {
        "url": config.VIN_DECODER_URL,
        "health_endpoint": "/health",
        "available": False
    },
    "fault-detector": {
        "url": config.FAULT_DETECTOR_URL, 
        "health_endpoint": "/health",
        "available": False
    },
    "diagnostic": {
        "url": config.DIAGNOSTIC_SERVICE_URL,
        "health_endpoint": "/health", 
        "available": False
    },
    "mqtt-bridge": {
        "url": config.MQTT_BRIDGE_URL,
        "health_endpoint": "/health",
        "available": False
    }
}

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    services: Dict[str, bool]

class ServiceStatus(BaseModel):
    service: str
    available: bool
    url: str
    response_time_ms: Optional[float] = None

async def check_service_health(service_name: str, service_config: Dict) -> bool:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_config['url']}{service_config['health_endpoint']}")
            is_healthy = response.status_code == 200
            service_config['available'] = is_healthy
            return is_healthy
    except Exception:
        service_config['available'] = False
        return False

async def health_check_all_services():
    """Check health of all registered services"""
    tasks = []
    for service_name, config in SERVICE_REGISTRY.items():
        task = check_service_health(service_name, config)
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)

async def proxy_request(service_url: str, path: str, method: str, **kwargs):
    """Proxy request to target service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{service_url}{path}"
            
            if method.upper() == "GET":
                response = await client.get(url, params=kwargs.get('params'))
            elif method.upper() == "POST":
                response = await client.post(url, json=kwargs.get('json'), params=kwargs.get('params'))
            elif method.upper() == "PUT":
                response = await client.put(url, json=kwargs.get('json'), params=kwargs.get('params'))
            elif method.upper() == "DELETE":
                response = await client.delete(url, params=kwargs.get('params'))
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return response
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Check service health on startup"""
    await health_check_all_services()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """API Gateway health check"""
    await health_check_all_services()
    
    service_status = {name: config['available'] for name, config in SERVICE_REGISTRY.items()}
    
    return HealthResponse(
        status="healthy",
        service="api-gateway",
        version="1.0.0",
        services=service_status
    )

@app.get("/api/gateway/services", response_model=List[ServiceStatus])
async def get_services():
    """Get status of all registered services"""
    await health_check_all_services()
    
    services = []
    for service_name, config in SERVICE_REGISTRY.items():
        services.append(ServiceStatus(
            service=service_name,
            available=config['available'],
            url=config['url']
        ))
    
    return services

# VIN Decoder Service Routes
@app.get("/api/vin/decode/{vin}")
async def decode_vin(vin: str):
    """Proxy VIN decoding to VIN decoder service"""
    if not SERVICE_REGISTRY['vin-decoder']['available']:
        raise HTTPException(status_code=503, detail="VIN decoder service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['vin-decoder']['url'],
        f"/api/vin/decode/{vin}",
        "GET"
    )
    
    return response.json()

@app.get("/api/vin/validate/{vin}")
async def validate_vin(vin: str):
    """Proxy VIN validation to VIN decoder service"""
    if not SERVICE_REGISTRY['vin-decoder']['available']:
        raise HTTPException(status_code=503, detail="VIN decoder service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['vin-decoder']['url'],
        f"/api/vin/validate/{vin}",
        "GET"
    )
    
    return response.json()

@app.get("/api/vin/recalls/{vin}")
async def get_recalls(vin: str):
    """Proxy recall lookup to VIN decoder service"""
    if not SERVICE_REGISTRY['vin-decoder']['available']:
        raise HTTPException(status_code=503, detail="VIN decoder service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['vin-decoder']['url'],
        f"/api/vin/recalls/{vin}",
        "GET"
    )
    
    return response.json()

# Fault Detector Service Routes
@app.post("/api/fault/analyze")
async def analyze_faults(request: Request):
    """Proxy fault analysis to fault detector service"""
    if not SERVICE_REGISTRY['fault-detector']['available']:
        raise HTTPException(status_code=503, detail="Fault detector service unavailable")
    
    body = await request.json()
    vehicle_id = request.query_params.get('vehicle_id', 'unknown')
    
    response = await proxy_request(
        SERVICE_REGISTRY['fault-detector']['url'],
        f"/api/fault/analyze?vehicle_id={vehicle_id}",
        "POST",
        json=body
    )
    
    return response.json()

@app.get("/api/fault/dtc/{code}")
async def analyze_dtc_code(code: str):
    """Proxy DTC analysis to fault detector service"""
    if not SERVICE_REGISTRY['fault-detector']['available']:
        raise HTTPException(status_code=503, detail="Fault detector service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['fault-detector']['url'],
        f"/api/fault/dtc/{code}",
        "GET"
    )
    
    return response.json()

@app.get("/api/fault/health-score")
async def calculate_health_score(request: Request):
    """Proxy health score calculation to fault detector service"""
    if not SERVICE_REGISTRY['fault-detector']['available']:
        raise HTTPException(status_code=503, detail="Fault detector service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['fault-detector']['url'],
        "/api/fault/health-score",
        "GET",
        params=dict(request.query_params)
    )
    
    return response.json()

# Diagnostic Service Routes
@app.post("/api/diagnostic/generate-report")
async def generate_diagnostic_report(request: Request):
    """Proxy diagnostic report generation to diagnostic service"""
    if not SERVICE_REGISTRY['diagnostic']['available']:
        raise HTTPException(status_code=503, detail="Diagnostic service unavailable")
    
    body = await request.json()
    
    response = await proxy_request(
        SERVICE_REGISTRY['diagnostic']['url'],
        "/api/diagnostic/generate-report",
        "POST",
        json=body
    )
    
    return response.json()

@app.get("/api/diagnostic/report/{report_id}")
async def get_report(report_id: str):
    """Proxy diagnostic report retrieval to diagnostic service"""
    if not SERVICE_REGISTRY['diagnostic']['available']:
        raise HTTPException(status_code=503, detail="Diagnostic service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['diagnostic']['url'],
        f"/api/diagnostic/report/{report_id}",
        "GET"
    )
    
    return response.json()

# MQTT Bridge Service Routes
@app.post("/api/mqtt/publish")
async def publish_mqtt(request: Request):
    """Proxy MQTT publishing to MQTT bridge service"""
    if not SERVICE_REGISTRY['mqtt-bridge']['available']:
        raise HTTPException(status_code=503, detail="MQTT bridge service unavailable")
    
    body = await request.json()
    
    response = await proxy_request(
        SERVICE_REGISTRY['mqtt-bridge']['url'],
        "/api/mqtt/publish",
        "POST",
        json=body
    )
    
    return response.json()

@app.get("/api/mqtt/sensor-data")
async def get_sensor_data(request: Request):
    """Proxy sensor data retrieval to MQTT bridge service"""
    if not SERVICE_REGISTRY['mqtt-bridge']['available']:
        raise HTTPException(status_code=503, detail="MQTT bridge service unavailable")
    
    response = await proxy_request(
        SERVICE_REGISTRY['mqtt-bridge']['url'],
        "/api/mqtt/sensor-data",
        "GET",
        params=dict(request.query_params)
    )
    
    return response.json()

@app.post("/api/mqtt/vehicle-data/{vehicle_id}")
async def receive_vehicle_data(vehicle_id: str, request: Request):
    """Proxy vehicle data to MQTT bridge service"""
    if not SERVICE_REGISTRY['mqtt-bridge']['available']:
        raise HTTPException(status_code=503, detail="MQTT bridge service unavailable")
    
    body = await request.json()
    
    response = await proxy_request(
        SERVICE_REGISTRY['mqtt-bridge']['url'],
        f"/api/mqtt/vehicle-data/{vehicle_id}",
        "POST",
        json=body
    )
    
    return response.json()

@app.get("/api/gateway/info")
async def gateway_info():
    """Get API Gateway information"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "description": "Central entry point for MOTOSPECT microservices",
        "registered_services": list(SERVICE_REGISTRY.keys()),
        "endpoints": {
            "vin": ["/api/vin/decode/{vin}", "/api/vin/validate/{vin}", "/api/vin/recalls/{vin}"],
            "fault": ["/api/fault/analyze", "/api/fault/dtc/{code}", "/api/fault/health-score"],
            "diagnostic": ["/api/diagnostic/generate-report", "/api/diagnostic/report/{report_id}"],
            "mqtt": ["/api/mqtt/publish", "/api/mqtt/sensor-data", "/api/mqtt/vehicle-data/{vehicle_id}"]
        },
        "port": int(os.getenv("PORT", config.API_GATEWAY_PORT))
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", config.API_GATEWAY_PORT))
    print(f"🚀 Starting API Gateway on port {port}")
    print("🔗 Available services:")
    for service_name, config in SERVICE_REGISTRY.items():
        print(f"   - {service_name}: {config['url']}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
