#!/usr/bin/env python3
"""Simple in-memory Scan Manager used by MotoSpect backend and tests."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional


class ScanManager:
    """Manage diagnostic scans in memory (suitable for development & testing)."""

    def __init__(self) -> None:
        self._scans: Dict[str, Dict] = {}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def create_scan(self, vehicle_id: Optional[str] = None) -> str:
        """Create a new scan and return its unique ID."""
        scan_id = str(uuid.uuid4())
        self._scans[scan_id] = {
            "vehicle_id": vehicle_id,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }
        return scan_id

    def get_scan_status(self, scan_id: str) -> str:
        """Return status for given scan or ``unknown`` if not found."""
        return self._scans.get(scan_id, {}).get("status", "unknown")

    def complete_scan(self, scan_id: str) -> None:
        """Mark scan as completed."""
        if scan_id in self._scans:
            self._scans[scan_id]["status"] = "completed"
            self._scans[scan_id]["completed_at"] = datetime.utcnow().isoformat()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def list_scans(self) -> Dict[str, Dict]:
        """Return all scans (debugging use only)."""
        return self._scans.copy()
