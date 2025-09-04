"""
Engine thresholds and specifications for different engine sizes
"""

from typing import Dict, Any


class EngineThresholds:
    """Engine parameter thresholds for different engine capacities"""
    
    @staticmethod
    def get_thresholds() -> Dict[str, Dict[str, Any]]:
        """Get thresholds for all engine sizes"""
        return {
            "1.0L": {
                "rpm_idle": (600, 900),
                "rpm_max": 6500,
                "oil_pressure_min": 20,
                "coolant_temp_normal": (80, 105),
                "fuel_pressure": (30, 45)
            },
            "1.5L": {
                "rpm_idle": (650, 950),
                "rpm_max": 6500,
                "oil_pressure_min": 22,
                "coolant_temp_normal": (82, 108),
                "fuel_pressure": (32, 48)
            },
            "2.0L": {
                "rpm_idle": (700, 1000),
                "rpm_max": 6000,
                "oil_pressure_min": 25,
                "coolant_temp_normal": (85, 110),
                "fuel_pressure": (35, 50)
            },
            "2.5L": {
                "rpm_idle": (700, 1000),
                "rpm_max": 5800,
                "oil_pressure_min": 28,
                "coolant_temp_normal": (85, 110),
                "fuel_pressure": (38, 52)
            },
            "3.0L": {
                "rpm_idle": (750, 1050),
                "rpm_max": 5500,
                "oil_pressure_min": 30,
                "coolant_temp_normal": (88, 112),
                "fuel_pressure": (40, 55)
            }
        }
    
    @staticmethod
    def get_threshold_for_engine(engine_size: str) -> Dict[str, Any]:
        """Get thresholds for specific engine size"""
        thresholds = EngineThresholds.get_thresholds()
        # Default to 2.0L if engine size not found
        return thresholds.get(engine_size, thresholds["2.0L"])
    
    @staticmethod
    def get_maintenance_intervals() -> Dict[str, int]:
        """Get maintenance intervals in miles"""
        return {
            "oil_change": 5000,
            "air_filter": 15000,
            "spark_plugs": 30000,
            "coolant_flush": 50000,
            "transmission_fluid": 60000,
            "brake_fluid": 30000,
            "power_steering_fluid": 75000,
            "differential_fluid": 60000,
            "fuel_filter": 30000,
            "cabin_air_filter": 15000
        }
