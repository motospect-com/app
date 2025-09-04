from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import uuid
import os
from typing import Dict, Any, Optional
from mqtt_bridge import mqtt_bridge
from vin_decoder import VINDecoder
from obd_interface import OBDInterface
from fault_detector import FaultDetector
from pydantic import BaseModel
import random
import numpy as np

app = FastAPI()

# CORS for local dev (React on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
vin_decoder = VINDecoder()
obd_interface = OBDInterface()
fault_detector = FaultDetector()


# Initialize MQTT bridge if enabled
@app.on_event("startup")
def on_startup():
    if os.getenv("ENABLE_MQTT_BRIDGE", "true").lower() == "true":
        mqtt_bridge.connect()


# --- Simple Scan Manager (in-memory) ---
class StartScanRequest(BaseModel):
    vehicle_id: Optional[str] = None
    notes: Optional[str] = None


class ScanManager:
    def __init__(self):
        self.active: Dict[str, Dict] = {}
        self.results: Dict[str, Dict] = {}

    def start(self, vehicle_id: Optional[str] = None) -> str:
        scan_id = str(uuid.uuid4())
        self.active[scan_id] = {
            "vehicle_id": vehicle_id,
            "started_at": datetime.now().isoformat(),
            "data": self._generate_scan_data()
        }
        return scan_id

    def stop(self, scan_id: str):
        if scan_id not in self.active:
            raise KeyError("scan_id not active")
        # Finalize by storing a last sample
        self.results[scan_id] = self._generate_scan_data()
        del self.active[scan_id]

    def _generate_scan_data(self):
        """Generate mock scan data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "audio_spectrum": np.random.rand(512).tolist(),
            "tof_profile": np.random.rand(256).tolist(),
            "status": "completed"
        }

    def get_results(self, scan_id: str) -> Dict:
        if scan_id in self.results:
            return self.results[scan_id]
        raise KeyError("no results for scan_id")


scan_mgr = ScanManager()

# Request/Response models
class VINDecodeRequest(BaseModel):
    vin: str


class ScanStartRequest(BaseModel):
    vin: str
    scan_type: str = "full"


class ReportGenerateRequest(BaseModel):
    vin: str
    scan_data: Optional[Dict[str, Any]] = None

# In-memory storage for reports (in production, use a database)
reports_storage = {}


@app.post("/api/vehicle/decode")
async def decode_vehicle(request: VINDecodeRequest):
    """Decode VIN and get vehicle information"""
    try:
        vehicle_info = await vin_decoder.decode_vin(request.vin)
        if not vehicle_info:
            msg = "Invalid VIN or decoding failed"
            raise HTTPException(status_code=400, detail=msg)
        return vehicle_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scan/start")
async def start_scan(request: ScanStartRequest):
    """Initiate vehicle scan"""
    try:
        # Start OBD scan
        scan_id = str(uuid.uuid4())
        asyncio.create_task(
            obd_interface.perform_diagnostic_scan(
                scan_id=scan_id,
                scan_type=request.scan_type
            )
        )
        return {"scan_id": scan_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/report/generate")
async def generate_report(request: ReportGenerateRequest):
    """Generate diagnostic report"""
    try:
        # Get vehicle info
        vehicle_info = await vin_decoder.decode_vin(request.vin)

        # Get OBD scan results  
        obd_params = await obd_interface.read_all_parameters()
        fault_codes = await obd_interface.read_fault_codes()
        
        # Run fault detection analysis
        engine_size = vehicle_info.get('engine_displacement', '2.0L') if vehicle_info else '2.0L'
        analysis = fault_detector.analyze_parameters(
            {'fault_codes': fault_codes, **obd_params},
            engine_size=engine_size
        )

        # Generate report ID
        report_id = str(uuid.uuid4())[:8].upper()

        # Create comprehensive report
        report_data = {
            "report_id": report_id,
            "scan_date": datetime.now().isoformat(),
            "vehicle": vehicle_info if vehicle_info else {},
            "system_health": {
                "Engine": {"value": 92, "status": "Good", 
                           "issues": []},
                "Transmission": {"value": 88, "status": "Good",
                                 "issues": []},
                "Brakes": {"value": 78, "status": "Fair",
                           "issues": ["Brake pads wearing"]},
                "Suspension": {"value": 85, "status": "Good",
                               "issues": []},
                "Electrical": {"value": 90, "status": "Good",
                               "issues": []},
                "Emissions": {"value": 95, "status": "Excellent",
                              "issues": []}
            },
            "overall_health": analysis.get('overall_health', random.randint(65, 95)),
            "systems": [
                {"name": "Engine", "health_percentage": random.randint(70, 100), "issue_count": random.randint(0, 3)},
                {"name": "Transmission", "health_percentage": random.randint(75, 100), "issue_count": random.randint(0, 2)},
                {"name": "Brakes", "health_percentage": random.randint(60, 100), "issue_count": random.randint(0, 2)},
                {"name": "Suspension", "health_percentage": random.randint(70, 100), "issue_count": random.randint(0, 2)},
                {"name": "Electrical", "health_percentage": random.randint(80, 100), "issue_count": random.randint(0, 1)},
                {"name": "Exhaust", "health_percentage": random.randint(85, 100), "issue_count": random.randint(0, 1)}
            ],
            "fault_codes": analysis.get('faults', [
                {
                    "code": "P0300",
                    "description": "Random/Multiple Cylinder Misfire Detected",
                    "severity": "moderate",
                    "system": "Engine",
                    "action": "Scheduled"
                }
            ]),
            "recommendations": [
                {"text": "Replace brake pads within next 5,000 miles",
                 "priority": "Medium", "cost": "$150-250"},
                {"text": "Schedule transmission fluid change",
                 "priority": "Low", "cost": "$80-120"},
                {"text": "Investigate cylinder misfire - may need spark plugs",
                 "priority": "High", "cost": "$100-200"}
            ],
            "issue_locations": [
                {"x": 290, "y": 180, "severity": "Medium", "description": "Engine - Minor oil leak"},
                {"x": 250, "y": 290, "severity": "Low", "description": "Front brakes - Wear detected"},
                {"x": 550, "y": 290, "severity": "Info", "description": "Rear suspension - Check recommended"}
            ],
            "ai_analysis": {
                "summary": (
                    "Based on the diagnostic scan, your vehicle is in good "
                    "overall condition with an 87% health score. The main area "
                    "of concern is the brake system showing moderate wear. The "
                    "P0300 code indicates a misfire that should be addressed "
                    "soon to prevent potential catalytic converter damage. "
                    "Regular maintenance will help maintain optimal performance."
                ),
                "findings": [
                    "Engine performance parameters within normal range",
                    "Brake wear is normal for current mileage",
                    "No emissions-related issues detected"
                ],
                "recommendations": [
                    "Schedule regular oil change within next 1000 km",
                    "Monitor brake pad thickness at next service",
                    "Consider transmission fluid check at 150,000km"
                ]
            }
        }

        # Store report
        reports_storage[report_id] = report_data

        return {"report_id": report_id, "status": "generated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    """Get diagnostic report by ID"""
    report = reports_storage.get(report_id.upper())
    if not report:
        msg = "Report not found"
        raise HTTPException(status_code=404, detail=msg)
    return report


@app.get("/api/obd/autodetect")
async def obd_autodetect():
    """Auto-detect vehicle via OBD connection"""
    try:
        vehicle_info = await obd_interface.get_vehicle_info()
        return vehicle_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- OLD ENDPOINT (deprecated but kept for compatibility) ---
@app.post("/upload/{device_type}")
def upload_data(device_type: str, data=None):
    _ = scan_mgr.start(vehicle_id=None)  # Start scan but don't use ID
    return {"status": "ongoing"}


@app.post("/api/scan/{scan_id}/stop")
def api_scan_stop(scan_id: str):
    try:
        scan_mgr.stop(scan_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Scan not found or not active")
    return {"scan_id": scan_id, "status": "stopped"}


@app.get("/api/scan/{scan_id}/status")
def api_scan_results(scan_id: str):
    try:
        data = scan_mgr.get_results(scan_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Results not found for scan_id")
    return {"status": "stopped", "final_data": data}
