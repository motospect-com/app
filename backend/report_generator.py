#!/usr/bin/env python3
"""Lightweight Report Generator for MotoSpect tests & development.

NOTE: In production this logic should be replaced by the dedicated
report-service microservice that renders a full PDF. Here we only need
basic functionality to satisfy unit tests and backend calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any


class ReportGenerator:  # pragma: no cover – simple stub
    """Generate JSON diagnostic reports.

    The `generate_report` method takes input data (already analysed) and
    returns a dictionary with a unique report ID and timestamp. It simply
    echoes back the data for testing purposes.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return report dictionary and persist it in memory."""
        report_id = str(uuid.uuid4()).upper()
        report = {
            "report_id": report_id,
            "generated_at": datetime.utcnow().isoformat(),
            **data,
        }
        self._storage[report_id] = report
        return report

    def get_report(self, report_id: str) -> Dict[str, Any] | None:
        """Retrieve report by ID if present."""
        return self._storage.get(report_id.upper())
