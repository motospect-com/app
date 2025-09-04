#!/usr/bin/env python3
"""
VIN Decoder Microservice
Independent service for VIN decoding functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import os
import sys
import uvicorn
from pathlib import Path

# Add backend path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from vin_decoder import VINDecoder
from external_apis import NHTSAApi

app = FastAPI(
    title="MOTOSPECT VIN Decoder Service",
    description="Microservice for VIN decoding and vehicle information retrieval",
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

# Global VIN decoder instance
vin_decoder = VINDecoder()

class VINRequest(BaseModel):
    vin: str
    
    @validator('vin')
    def validate_vin(cls, v):
        if len(v) != 17:
            raise ValueError('VIN must be exactly 17 characters')
        if not v.replace('-', '').isalnum():
            raise ValueError('VIN contains invalid characters')
        return v.upper()

class VehicleInfo(BaseModel):
    vin: str
    make: str
    model: str
    year: int
    body_type: str = None
    engine_info: str = None
    transmission: str = None
    fuel_type: str = None
    manufacturer: str = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    port: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="vin-decoder-service",
        version="1.0.0",
        port=int(os.getenv("PORT", "8001"))
    )

@app.get("/api/vin/decode/{vin}", response_model=VehicleInfo)
async def decode_vin(vin: str):
    """Decode VIN to vehicle information"""
    try:
        # Validate VIN format
        if len(vin) != 17:
            raise HTTPException(status_code=400, detail="VIN must be exactly 17 characters")
        
        # Decode VIN using the existing decoder
        vehicle_data = vin_decoder.decode_vin(vin)
        
        if not vehicle_data:
            raise HTTPException(status_code=404, detail="Vehicle information not found")
        
        return VehicleInfo(
            vin=vin,
            make=vehicle_data.get('make', 'Unknown'),
            model=vehicle_data.get('model', 'Unknown'),
            year=vehicle_data.get('year', 0),
            body_type=vehicle_data.get('body_type'),
            engine_info=vehicle_data.get('engine_info'),
            transmission=vehicle_data.get('transmission'),
            fuel_type=vehicle_data.get('fuel_type'),
            manufacturer=vehicle_data.get('manufacturer')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding VIN: {str(e)}")

@app.get("/api/vin/validate/{vin}")
async def validate_vin(vin: str):
    """Validate VIN format"""
    try:
        is_valid = vin_decoder.validate_vin(vin)
        return {
            "vin": vin,
            "valid": is_valid,
            "message": "Valid VIN format" if is_valid else "Invalid VIN format"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating VIN: {str(e)}")

@app.get("/api/vin/recalls/{vin}")
async def get_recalls(vin: str):
    """Get recall information for VIN"""
    try:
        if len(vin) != 17:
            raise HTTPException(status_code=400, detail="VIN must be exactly 17 characters")
        
        recalls = vin_decoder.get_recalls(vin)
        return {
            "vin": vin,
            "recalls": recalls if recalls else [],
            "count": len(recalls) if recalls else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recalls: {str(e)}")

@app.get("/api/vin/info")
async def service_info():
    """Get service information"""
    return {
        "service": "VIN Decoder Service",
        "version": "1.0.0",
        "description": "Independent microservice for VIN decoding",
        "endpoints": [
            "/health",
            "/api/vin/decode/{vin}",
            "/api/vin/validate/{vin}",
            "/api/vin/recalls/{vin}"
        ],
        "port": int(os.getenv("PORT", "8001"))
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    print(f"🚀 Starting VIN Decoder Service on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
