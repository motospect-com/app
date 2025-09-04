#!/usr/bin/env python3
"""
Simple test server for MOTOSPECT backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fault_detector import FaultDetector
from vin_decoder import VINDecoder
import uvicorn

app = FastAPI(title="MOTOSPECT Test API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
fault_detector = FaultDetector()
vin_decoder = VINDecoder()

@app.get("/")
async def root():
    return {"message": "MOTOSPECT Test API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "motospect-backend",
        "version": "1.0.0",
        "modules": {
            "fault_detector": "✓ Loaded",
            "vin_decoder": "✓ Loaded"
        }
    }

@app.post("/api/analyze-faults")
async def analyze_faults(data: dict):
    """Test fault analysis with refactored modules"""
    try:
        fault_codes = data.get("fault_codes", [])
        parameters = data.get("parameters", {})
        
        # Use refactored FaultDetector
        analysis = fault_detector.analyze_fault_codes(fault_codes)
        health_scores = fault_detector.calculate_health_scores(parameters, fault_codes)
        
        return {
            "analysis": analysis,
            "health_scores": health_scores,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vin/decode/{vin}")
async def decode_vin(vin: str):
    """Test VIN decoding"""
    try:
        result = vin_decoder.decode_vin(vin)
        return {"vin": vin, "decoded": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting MOTOSPECT Test Server...")
    uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")
