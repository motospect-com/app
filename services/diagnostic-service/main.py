#!/usr/bin/env python3
"""
Diagnostic Service Microservice
Independent service for generating comprehensive diagnostic reports
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import sys
import uvicorn
import requests
from pathlib import Path
from datetime import datetime
import json

# Add backend path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

app = FastAPI(
    title="MOTOSPECT Diagnostic Service",
    description="Microservice for generating comprehensive vehicle diagnostic reports",
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

class DiagnosticRequest(BaseModel):
    vin: str = Field(..., description="Vehicle VIN number")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    engine_size: float = Field(..., description="Engine size in liters")
    rpm: int = Field(..., description="Current RPM")
    coolant_temp: float = Field(..., description="Coolant temperature in Celsius")
    oil_pressure: float = Field(..., description="Oil pressure in bar")
    fuel_pressure: float = Field(..., description="Fuel pressure in bar")
    voltage: float = Field(default=12.0, description="Battery voltage")
    mileage: int = Field(default=0, description="Vehicle mileage in km")
    dtc_codes: List[str] = Field(default=[], description="DTC fault codes")
    customer_name: str = Field(default="", description="Customer name")
    technician_notes: str = Field(default="", description="Technician notes")

class DiagnosticReport(BaseModel):
    report_id: str
    timestamp: str
    vehicle_info: Dict
    fault_analysis: Dict
    health_assessment: Dict
    recommendations: List[str]
    next_service_date: str
    report_summary: str
    pdf_url: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    port: int

# Service discovery - get other service URLs
def get_service_url(service_name: str, default_port: int) -> str:
    """Get service URL with fallback to default port"""
    base_url = f"http://localhost:{default_port}"
    return base_url

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="diagnostic-service",
        version="1.0.0",
        port=int(os.getenv("PORT", "8003"))
    )

@app.post("/api/diagnostic/generate-report", response_model=DiagnosticReport)
async def generate_diagnostic_report(request: DiagnosticRequest):
    """Generate comprehensive diagnostic report"""
    try:
        report_id = f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.vehicle_id}"
        timestamp = datetime.now().isoformat()
        
        # Get vehicle info from VIN decoder service
        vin_service_url = get_service_url("vin-decoder-service", 8001)
        vehicle_info = {}
        try:
            vin_response = requests.get(f"{vin_service_url}/api/vin/decode/{request.vin}", timeout=5)
            if vin_response.status_code == 200:
                vehicle_info = vin_response.json()
        except Exception as e:
            print(f"Warning: Could not get vehicle info: {e}")
            vehicle_info = {
                "vin": request.vin,
                "make": "Unknown",
                "model": "Unknown",
                "year": 0
            }
        
        # Get fault analysis from fault detector service
        fault_service_url = get_service_url("fault-detector-service", 8002)
        fault_analysis = {}
        try:
            fault_payload = {
                "engine_size": request.engine_size,
                "rpm": request.rpm,
                "coolant_temp": request.coolant_temp,
                "oil_pressure": request.oil_pressure,
                "fuel_pressure": request.fuel_pressure,
                "voltage": request.voltage,
                "mileage": request.mileage,
                "dtc_codes": request.dtc_codes
            }
            
            fault_response = requests.post(
                f"{fault_service_url}/api/fault/analyze?vehicle_id={request.vehicle_id}",
                json=fault_payload,
                timeout=10
            )
            if fault_response.status_code == 200:
                fault_analysis = fault_response.json()
        except Exception as e:
            print(f"Warning: Could not get fault analysis: {e}")
            fault_analysis = {
                "detected_faults": [],
                "health_scores": {},
                "recommendations": [],
                "severity_level": "unknown"
            }
        
        # Generate health assessment
        health_scores = fault_analysis.get("health_scores", {})
        overall_score = sum(health_scores.values()) // len(health_scores) if health_scores else 75
        
        health_assessment = {
            "overall_score": overall_score,
            "status": get_health_status(overall_score),
            "individual_scores": health_scores,
            "critical_issues": len([f for f in fault_analysis.get("detected_faults", []) 
                                  if f.get("severity") == "Critical"]),
            "warnings": len([f for f in fault_analysis.get("detected_faults", []) 
                            if f.get("severity") in ["High", "Moderate"]])
        }
        
        # Generate recommendations
        recommendations = fault_analysis.get("recommendations", [])
        if not recommendations:
            recommendations = generate_default_recommendations(request.mileage, overall_score)
        
        # Calculate next service date
        next_service_date = calculate_next_service_date(request.mileage, fault_analysis.get("detected_faults", []))
        
        # Generate report summary
        report_summary = generate_report_summary(
            vehicle_info, 
            health_assessment, 
            fault_analysis.get("detected_faults", []),
            recommendations
        )
        
        return DiagnosticReport(
            report_id=report_id,
            timestamp=timestamp,
            vehicle_info=vehicle_info,
            fault_analysis=fault_analysis,
            health_assessment=health_assessment,
            recommendations=recommendations,
            next_service_date=next_service_date,
            report_summary=report_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating diagnostic report: {str(e)}")

@app.get("/api/diagnostic/report/{report_id}")
async def get_report(report_id: str):
    """Get diagnostic report by ID"""
    # In a real implementation, this would fetch from database
    return {"message": f"Report {report_id} would be retrieved from database"}

@app.get("/api/diagnostic/reports/vehicle/{vehicle_id}")
async def get_vehicle_reports(vehicle_id: str):
    """Get all reports for a vehicle"""
    # In a real implementation, this would fetch from database
    return {"message": f"Reports for vehicle {vehicle_id} would be retrieved from database"}

@app.get("/api/diagnostic/info")
async def service_info():
    """Get service information"""
    return {
        "service": "Diagnostic Service",
        "version": "1.0.0",
        "description": "Independent microservice for diagnostic report generation",
        "endpoints": [
            "/health",
            "/api/diagnostic/generate-report",
            "/api/diagnostic/report/{report_id}",
            "/api/diagnostic/reports/vehicle/{vehicle_id}"
        ],
        "port": int(os.getenv("PORT", "8003")),
        "dependencies": ["vin-decoder-service", "fault-detector-service"]
    }

def get_health_status(score: int) -> str:
    """Convert health score to status"""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score >= 30:
        return "Poor"
    else:
        return "Critical"

def generate_default_recommendations(mileage: int, health_score: int) -> List[str]:
    """Generate default maintenance recommendations"""
    recommendations = []
    
    if mileage > 0:
        if mileage % 10000 < 1000:  # Close to 10k interval
            recommendations.append("Regular service due - oil change and basic inspection")
        
        if mileage > 50000 and mileage % 20000 < 2000:
            recommendations.append("Major service recommended - transmission and brake system check")
    
    if health_score < 60:
        recommendations.append("Immediate inspection recommended due to low health score")
    
    if not recommendations:
        recommendations.append("Continue regular maintenance schedule")
    
    return recommendations

def calculate_next_service_date(mileage: int, faults: List[Dict]) -> str:
    """Calculate next recommended service date"""
    from datetime import datetime, timedelta
    
    # Base interval: 6 months
    base_days = 180
    
    # Adjust based on faults
    critical_faults = len([f for f in faults if f.get("severity") == "Critical"])
    if critical_faults > 0:
        base_days = 30  # 1 month if critical issues
    elif any(f.get("severity") == "High" for f in faults):
        base_days = 90  # 3 months if high severity issues
    
    next_date = datetime.now() + timedelta(days=base_days)
    return next_date.strftime("%Y-%m-%d")

def generate_report_summary(vehicle_info: Dict, health_assessment: Dict, faults: List[Dict], recommendations: List[str]) -> str:
    """Generate human-readable report summary"""
    make_model = f"{vehicle_info.get('make', 'Unknown')} {vehicle_info.get('model', 'Unknown')}"
    year = vehicle_info.get('year', 'Unknown')
    health_status = health_assessment.get('status', 'Unknown')
    score = health_assessment.get('overall_score', 0)
    
    critical_count = health_assessment.get('critical_issues', 0)
    warning_count = health_assessment.get('warnings', 0)
    
    summary = f"Diagnostic Report for {year} {make_model}\n\n"
    summary += f"Overall Health: {health_status} ({score}/100)\n"
    
    if critical_count > 0:
        summary += f"⚠️  {critical_count} critical issue(s) detected - immediate attention required\n"
    
    if warning_count > 0:
        summary += f"📋 {warning_count} warning(s) - monitor closely\n"
    
    if not critical_count and not warning_count:
        summary += "✅ No major issues detected\n"
    
    summary += f"\nRecommendations:\n"
    for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
        summary += f"{i}. {rec}\n"
    
    return summary

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    print(f"🚀 Starting Diagnostic Service on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
