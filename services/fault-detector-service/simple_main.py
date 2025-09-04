#!/usr/bin/env python3
"""
Simple Fault Detector Microservice - Working Version
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="MOTOSPECT Fault Detector Service",
    description="Microservice for vehicle fault detection and analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Fault Detector Service",
        "version": "1.0.0",
        "port": int(os.getenv("PORT", "8002"))
    }

@app.get("/")
def service_info():
    return {
        "service": "Fault Detector Service",
        "version": "1.0.0",
        "description": "Vehicle fault detection and analysis",
        "endpoints": ["/health", "/api/fault/analyze", "/api/fault/codes"],
        "port": int(os.getenv("PORT", "8002"))
    }

@app.post("/api/fault/analyze")
def analyze_faults(data: dict = {}):
    return {
        "faults": [],
        "health_score": 85,
        "recommendations": ["Regular maintenance check"],
        "source": "simplified"
    }

@app.get("/api/fault/codes")
def get_fault_codes():
    return {
        "codes": ["P0300", "P0420"],
        "definitions": {
            "P0300": "Random/Multiple Cylinder Misfire Detected",
            "P0420": "Catalyst System Efficiency Below Threshold"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    print(f"🚀 Starting Fault Detector Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
