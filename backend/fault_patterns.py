"""
Fault patterns and codes definitions for vehicle diagnostics
"""

from typing import Dict, List, Any
from enum import Enum


class FaultSeverity(Enum):
    """Fault severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INFO = "info"


class SystemType(Enum):
    """Vehicle system types"""
    ENGINE = "Engine"
    TRANSMISSION = "Transmission"
    BRAKES = "Brakes"
    SUSPENSION = "Suspension"
    ELECTRICAL = "Electrical"
    EMISSIONS = "Emissions"
    COOLING = "Cooling"
    FUEL = "Fuel"


class FaultPatterns:
    """Common fault patterns database"""
    
    @staticmethod
    def get_patterns() -> Dict[str, Dict[str, Any]]:
        """Get all fault patterns"""
        return {
            "P0300": {
                "description": "Random/Multiple Cylinder Misfire",
                "system": SystemType.ENGINE,
                "severity": FaultSeverity.HIGH,
                "causes": [
                    "Worn spark plugs",
                    "Faulty ignition coils",
                    "Vacuum leak",
                    "Low fuel pressure",
                    "Clogged fuel injectors"
                ],
                "immediate_action": True
            },
            "P0171": {
                "description": "System Too Lean (Bank 1)",
                "system": SystemType.FUEL,
                "severity": FaultSeverity.MODERATE,
                "causes": [
                    "Vacuum leak",
                    "Faulty MAF sensor",
                    "Clogged fuel filter",
                    "Weak fuel pump"
                ],
                "immediate_action": False
            },
            "P0420": {
                "description": "Catalyst System Efficiency Below Threshold",
                "system": SystemType.EMISSIONS,
                "severity": FaultSeverity.MODERATE,
                "causes": [
                    "Failing catalytic converter",
                    "Engine misfire",
                    "Rich/lean mixture",
                    "Oxygen sensor fault"
                ],
                "immediate_action": False
            },
            "P0128": {
                "description": "Coolant Temperature Below Thermostat Regulating Temp",
                "system": SystemType.COOLING,
                "severity": FaultSeverity.LOW,
                "causes": [
                    "Stuck open thermostat",
                    "Low coolant level",
                    "Faulty coolant temperature sensor"
                ],
                "immediate_action": False
            },
            "P0442": {
                "description": "EVAP System Small Leak Detected",
                "system": SystemType.EMISSIONS,
                "severity": FaultSeverity.LOW,
                "causes": [
                    "Loose gas cap",
                    "Small leak in EVAP system",
                    "Faulty purge valve"
                ],
                "immediate_action": False
            },
            "P0401": {
                "description": "EGR Flow Insufficient",
                "system": SystemType.EMISSIONS,
                "severity": FaultSeverity.MODERATE,
                "causes": [
                    "Clogged EGR passages",
                    "Faulty EGR valve",
                    "Carbon buildup"
                ],
                "immediate_action": False
            },
            "P0700": {
                "description": "Transmission Control System Malfunction",
                "system": SystemType.TRANSMISSION,
                "severity": FaultSeverity.HIGH,
                "causes": [
                    "Transmission fluid issues",
                    "Faulty transmission control module",
                    "Wiring problems"
                ],
                "immediate_action": True
            },
            "P0500": {
                "description": "Vehicle Speed Sensor Malfunction",
                "system": SystemType.TRANSMISSION,
                "severity": FaultSeverity.MODERATE,
                "causes": [
                    "Faulty speed sensor",
                    "Wiring issues",
                    "ABS module problem"
                ],
                "immediate_action": False
            },
            "P0135": {
                "description": "O2 Sensor Heater Circuit Malfunction",
                "system": SystemType.EMISSIONS,
                "severity": FaultSeverity.MODERATE,
                "causes": [
                    "Faulty oxygen sensor",
                    "Blown fuse",
                    "Wiring problem"
                ],
                "immediate_action": False
            },
            "P0301": {
                "description": "Cylinder 1 Misfire Detected",
                "system": SystemType.ENGINE,
                "severity": FaultSeverity.HIGH,
                "causes": [
                    "Spark plug issue",
                    "Ignition coil failure",
                    "Fuel injector problem",
                    "Compression loss"
                ],
                "immediate_action": True
            }
        }
    
    @staticmethod
    def get_severity_order() -> Dict[FaultSeverity, int]:
        """Get severity priority order"""
        return {
            FaultSeverity.CRITICAL: 5,
            FaultSeverity.HIGH: 4,
            FaultSeverity.MODERATE: 3,
            FaultSeverity.LOW: 2,
            FaultSeverity.INFO: 1
        }
