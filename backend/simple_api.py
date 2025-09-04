#!/usr/bin/env python3
"""
Simple MOTOSPECT API with CORS support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fault_detector import FaultDetector
from vin_decoder import VINDecoder
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MOTOSPECT API",
    description="Vehicle diagnostic system",
    version="1.0.0"
)

# Configure CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize components
try:
    fault_detector = FaultDetector()
    vin_decoder = VINDecoder()
    logger.info("✓ Components initialized successfully")
except Exception as e:
    logger.error(f"✗ Failed to initialize components: {e}")
    fault_detector = None
    vin_decoder = None

@app.get("/")
async def root():
    return {
        "message": "MOTOSPECT API v1.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/vin/decode/{vin}",
            "/api/analyze-faults"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "motospect-backend",
        "version": "1.0.0",
        "port": 8030,
        "components": {
            "fault_detector": "✓ Loaded" if fault_detector else "✗ Failed",
            "vin_decoder": "✓ Loaded" if vin_decoder else "✗ Failed"
        }
    }

@app.get("/api/vin/decode/{vin}")
async def decode_vin(vin: str):
    """Decode VIN number"""
    try:
        if not vin_decoder:
            raise HTTPException(status_code=503, detail="VIN decoder not available")
        
        result = vin_decoder.decode_vin(vin)
        return {
            "vin": vin,
            "decoded": result,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"VIN decode error: {e}")
        raise HTTPException(status_code=500, detail=f"VIN decode failed: {str(e)}")

@app.post("/api/analyze-faults")
async def analyze_faults(data: dict):
    """Analyze fault codes"""
    try:
        if not fault_detector:
            raise HTTPException(status_code=503, detail="Fault detector not available")
        
        fault_codes = data.get("fault_codes", [])
        parameters = data.get("parameters", {})
        
        analysis = fault_detector.analyze_fault_codes(fault_codes)
        health_scores = fault_detector.calculate_health_scores(parameters, fault_codes)
        
        return {
            "analysis": analysis,
            "health_scores": health_scores,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Fault analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}

if __name__ == "__main__":
    logger.info("🚀 Starting MOTOSPECT API on port 8030...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8030, 
        log_level="info",
        access_log=True
    )
