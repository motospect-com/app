#!/usr/bin/env python3
"""
Fault Detector Microservice
Independent service for vehicle fault detection and analysis
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import sys
import uvicorn
from pathlib import Path

# Add backend path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from fault_detector import FaultDetector

app = FastAPI(
    title="MOTOSPECT Fault Detector Service",
    description="Microservice for vehicle fault detection and diagnostic analysis",
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

# Global fault detector instance
fault_detector = FaultDetector()

class VehicleParameters(BaseModel):
    engine_size: float = Field(..., description="Engine size in liters")
    rpm: int = Field(..., description="Current RPM")
    coolant_temp: float = Field(..., description="Coolant temperature in Celsius")
    oil_pressure: float = Field(..., description="Oil pressure in bar")
    fuel_pressure: float = Field(..., description="Fuel pressure in bar")
    voltage: float = Field(default=12.0, description="Battery voltage")
    mileage: int = Field(default=0, description="Vehicle mileage in km")
    dtc_codes: List[str] = Field(default=[], description="DTC fault codes")

class FaultAnalysisResult(BaseModel):
    vehicle_id: str
    analysis_timestamp: str
    detected_faults: List[Dict]
    health_scores: Dict[str, int]
    recommendations: List[str]
    severity_level: str
    next_service_km: int

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
        service="fault-detector-service", 
        version="1.0.0",
        port=int(os.getenv("PORT", "8002"))
    )

@app.post("/api/fault/analyze", response_model=FaultAnalysisResult)
async def analyze_faults(
    vehicle_id: str,
    parameters: VehicleParameters
):
    """Analyze vehicle parameters for faults"""
    try:
        # Convert parameters to the format expected by fault_detector
        param_dict = {
            'engine_size': parameters.engine_size,
            'rpm': parameters.rpm,
            'coolant_temp': parameters.coolant_temp,
            'oil_pressure': parameters.oil_pressure,
            'fuel_pressure': parameters.fuel_pressure,
            'voltage': parameters.voltage,
            'mileage': parameters.mileage
        }
        
        # Analyze faults using existing detector
        faults = fault_detector.analyze_parameters(param_dict)
        
        # Analyze DTC codes if provided
        dtc_analysis = []
        if parameters.dtc_codes:
            for code in parameters.dtc_codes:
                dtc_info = fault_detector.analyze_dtc_code(code)
                if dtc_info:
                    dtc_analysis.append(dtc_info)
        
        # Get health scores
        health_scores = fault_detector.calculate_health_scores(param_dict)
        
        # Get recommendations
        recommendations = fault_detector.get_recommendations(faults, parameters.mileage)
        
        # Calculate severity
        severity_level = fault_detector.calculate_overall_severity(faults + dtc_analysis)
        
        # Calculate next service interval
        next_service_km = fault_detector.calculate_next_service(parameters.mileage, faults)
        
        return FaultAnalysisResult(
            vehicle_id=vehicle_id,
            analysis_timestamp=fault_detector.get_timestamp(),
            detected_faults=faults + dtc_analysis,
            health_scores=health_scores,
            recommendations=recommendations,
            severity_level=severity_level,
            next_service_km=next_service_km
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing faults: {str(e)}")

@app.get("/api/fault/dtc/{code}")
async def analyze_dtc_code(code: str):
    """Analyze specific DTC fault code"""
    try:
        dtc_info = fault_detector.analyze_dtc_code(code)
        if not dtc_info:
            raise HTTPException(status_code=404, detail=f"DTC code {code} not found")
        
        return {
            "dtc_code": code,
            "analysis": dtc_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing DTC code: {str(e)}")

@app.get("/api/fault/thresholds/{engine_size}")
async def get_thresholds(engine_size: float):
    """Get fault detection thresholds for specific engine size"""
    try:
        thresholds = fault_detector.get_thresholds_for_engine(engine_size)
        return {
            "engine_size": engine_size,
            "thresholds": thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thresholds: {str(e)}")

@app.get("/api/fault/health-score")
async def calculate_health_score(
    rpm: int,
    coolant_temp: float,
    oil_pressure: float,
    fuel_pressure: float,
    voltage: float = 12.0,
    mileage: int = 0
):
    """Calculate vehicle health score from parameters"""
    try:
        parameters = {
            'rpm': rpm,
            'coolant_temp': coolant_temp,
            'oil_pressure': oil_pressure,
            'fuel_pressure': fuel_pressure,
            'voltage': voltage,
            'mileage': mileage
        }
        
        health_scores = fault_detector.calculate_health_scores(parameters)
        overall_score = sum(health_scores.values()) // len(health_scores)
        
        return {
            "parameters": parameters,
            "health_scores": health_scores,
            "overall_score": overall_score,
            "status": fault_detector.get_health_status(overall_score)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating health score: {str(e)}")

@app.get("/api/fault/info")
async def service_info():
    """Get service information"""
    return {
        "service": "Fault Detector Service",
        "version": "1.0.0", 
        "description": "Independent microservice for vehicle fault detection",
        "endpoints": [
            "/health",
            "/api/fault/analyze",
            "/api/fault/dtc/{code}",
            "/api/fault/thresholds/{engine_size}",
            "/api/fault/health-score"
        ],
        "port": int(os.getenv("PORT", "8002")),
        "supported_engine_sizes": "1.0L - 3.0L"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    print(f"🚀 Starting Fault Detector Service on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
