"""
Health score calculator for vehicle systems
"""

from typing import Dict, List, Any, Optional
from fault_patterns import FaultSeverity, SystemType
import numpy as np


class HealthCalculator:
    """Calculates health scores for vehicle systems"""
    
    def __init__(self):
        self.severity_weights = {
            FaultSeverity.CRITICAL: 0.0,
            FaultSeverity.HIGH: 0.3,
            FaultSeverity.MODERATE: 0.6,
            FaultSeverity.LOW: 0.8,
            FaultSeverity.INFO: 0.95
        }
    
    def calculate_health_scores(self, faults: List[Dict], 
                               parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Calculate health scores for all vehicle systems"""
        # Initialize all systems with perfect health
        health_scores = {
            SystemType.ENGINE.value: 100,
            SystemType.TRANSMISSION.value: 100,
            SystemType.BRAKES.value: 100,
            SystemType.SUSPENSION.value: 100,
            SystemType.ELECTRICAL.value: 100,
            SystemType.EMISSIONS.value: 100,
            SystemType.COOLING.value: 100,
            SystemType.FUEL.value: 100
        }
        
        # Reduce scores based on faults
        for fault in faults:
            system = fault.get("system")
            severity = fault.get("severity")
            
            if system and severity:
                current_score = health_scores.get(system, 100)
                weight = self.severity_weights.get(severity, 1.0)
                # Reduce score based on severity
                health_scores[system] = min(current_score, weight * 100)
        
        # Further adjust based on parameters if available
        if parameters:
            health_scores = self._adjust_scores_by_parameters(health_scores, parameters)
        
        # Calculate overall health
        overall_health = np.mean(list(health_scores.values()))
        
        return {
            "overall": round(overall_health, 1),
            "systems": health_scores,
            "status": self._get_health_status(overall_health)
        }
    
    def _adjust_scores_by_parameters(self, scores: Dict[str, float], 
                                    parameters: Dict[str, Any]) -> Dict[str, float]:
        """Adjust health scores based on sensor parameters"""
        # Engine health adjustments
        rpm = parameters.get("rpm")
        if rpm and rpm > 5000:
            scores[SystemType.ENGINE.value] *= 0.95
        
        # Cooling system adjustments
        coolant_temp = parameters.get("coolant_temp")
        if coolant_temp:
            if coolant_temp > 110:
                scores[SystemType.COOLING.value] *= 0.7
            elif coolant_temp < 70:
                scores[SystemType.COOLING.value] *= 0.9
        
        # Fuel system adjustments
        fuel_pressure = parameters.get("fuel_pressure")
        if fuel_pressure:
            if fuel_pressure < 30 or fuel_pressure > 60:
                scores[SystemType.FUEL.value] *= 0.85
        
        return scores
    
    def _get_health_status(self, overall_health: float) -> str:
        """Get health status description"""
        if overall_health >= 90:
            return "Excellent"
        elif overall_health >= 75:
            return "Good"
        elif overall_health >= 60:
            return "Fair"
        elif overall_health >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical trends for predictive maintenance"""
        if not historical_data or len(historical_data) < 2:
            return {"trend": "insufficient_data"}
        
        trends = {}
        parameters_to_track = ["rpm", "coolant_temp", "oil_pressure", "fuel_pressure"]
        
        for param in parameters_to_track:
            values = [d.get(param) for d in historical_data if d.get(param) is not None]
            if len(values) >= 2:
                values_array = np.array(values)
                trend = np.polyfit(range(len(values)), values, 1)[0]
                
                trends[param] = {
                    "direction": "increasing" if trend > 0 else "decreasing",
                    "rate": abs(trend),
                    "current": values[-1],
                    "average": np.mean(values_array),
                    "min": np.min(values_array),
                    "max": np.max(values_array)
                }
        
        return trends
