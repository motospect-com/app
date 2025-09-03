from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uuid

import websocket_handler
from data_generator import generate_scan_data


app = FastAPI()

# CORS for local dev (React on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"]
)

app.include_router(websocket_handler.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Motospect API"}


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
        }
        # Seed with an initial sample for demo/MVP
        self.results[scan_id] = generate_scan_data()
        return scan_id

    def stop(self, scan_id: str) -> None:
        if scan_id not in self.active:
            raise KeyError("scan_id not active")
        # Finalize by storing a last sample
        self.results[scan_id] = generate_scan_data()
        del self.active[scan_id]

    def get_results(self, scan_id: str) -> Dict:
        if scan_id in self.results:
            return self.results[scan_id]
        raise KeyError("no results for scan_id")


scan_mgr = ScanManager()


@app.post("/api/scan/start")
def api_scan_start(req: StartScanRequest):
    scan_id = scan_mgr.start(vehicle_id=req.vehicle_id)
    return {"scan_id": scan_id, "status": "scanning"}


@app.post("/api/scan/stop/{scan_id}")
def api_scan_stop(scan_id: str):
    try:
        scan_mgr.stop(scan_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Scan not found or not active")
    return {"scan_id": scan_id, "status": "stopped"}


@app.get("/api/scan/{scan_id}/results")
def api_scan_results(scan_id: str):
    try:
        return {"scan_id": scan_id, "data": scan_mgr.get_results(scan_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="Results not found for scan_id")
