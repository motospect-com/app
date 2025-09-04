#!/usr/bin/env python3
"""
Simple VIN Decoder Microservice - Working Version
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add paths for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
infrastructure_path = Path(__file__).parent.parent.parent / "infrastructure"
sys.path.append(str(backend_path))
sys.path.append(str(infrastructure_path))

# Create FastAPI app
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

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VIN Decoder Service",
        "version": "1.0.0",
        "port": int(os.getenv("PORT", "8001"))
    }

@app.get("/")
def service_info():
    """Service information endpoint"""
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

@app.get("/api/vin/validate/{vin}")
def validate_vin(vin: str):
    """Validate VIN format"""
    # Simple VIN validation
    if len(vin) != 17:
        return {"valid": False, "error": "VIN must be 17 characters"}
    
    # VIN should not contain I, O, or Q
    if any(char in vin.upper() for char in "IOQ"):
        return {"valid": False, "error": "VIN cannot contain I, O, or Q"}
    
    return {"valid": True, "vin": vin.upper()}

@app.get("/api/vin/decode/{vin}")
def decode_vin(vin: str):
    """Decode VIN (simplified version)"""
    validation = validate_vin(vin)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    # Simplified decode
    return {
        "vin": vin.upper(),
        "valid": True,
        "make": "Honda",  # Simplified
        "model": "Civic",
        "year": 2020,
        "body_type": "Sedan",
        "engine_size": 2.0,
        "fuel_type": "Gasoline",
        "source": "simplified"
    }

@app.get("/api/vin/recalls/{vin}")  
def get_recalls(vin: str):
    """Get recall information (simplified)"""
    validation = validate_vin(vin)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    return {
        "vin": vin.upper(),
        "recalls": [],
        "total_recalls": 0,
        "source": "simplified"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    print(f"🚀 Starting VIN Decoder Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
