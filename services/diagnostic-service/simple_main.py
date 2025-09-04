#!/usr/bin/env python3
"""
Simple Diagnostic Service - Working Version
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="MOTOSPECT Diagnostic Service",
    description="Microservice for vehicle diagnostic reporting",
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
        "service": "Diagnostic Service",
        "version": "1.0.0",
        "port": int(os.getenv("PORT", "8003"))
    }

@app.get("/")
def service_info():
    return {
        "service": "Diagnostic Service", 
        "version": "1.0.0",
        "description": "Vehicle diagnostic report generation",
        "endpoints": ["/health", "/api/diagnostic/report", "/api/diagnostic/summary"],
        "port": int(os.getenv("PORT", "8003"))
    }

@app.post("/api/diagnostic/report")
def generate_report(data: dict = {}):
    return {
        "report_id": "DIAG-001",
        "timestamp": "2025-09-04T21:30:00Z",
        "vehicle_health": {
            "overall_score": 82,
            "engine": 85,
            "transmission": 90,
            "brakes": 75,
            "electrical": 80
        },
        "recommendations": [
            "Check brake fluid level",
            "Replace air filter",
            "Schedule routine maintenance"
        ],
        "source": "simplified"
    }

@app.get("/api/diagnostic/summary")
def get_summary():
    return {
        "total_diagnostics": 156,
        "active_issues": 3,
        "resolved_issues": 12,
        "average_health_score": 84.5
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    print(f"🚀 Starting Diagnostic Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
