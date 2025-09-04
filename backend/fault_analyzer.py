"""
Fault analysis and recommendation engine
"""

from typing import Dict, List, Any, Optional
from fault_patterns import FaultSeverity, SystemType, FaultPatterns
from engine_thresholds import EngineThresholds
import numpy as np


class FaultAnalyzer:
    """Analyzes faults and generates recommendations"""
    
    def __init__(self):
        self.fault_patterns = FaultPatterns.get_patterns()
        self.thresholds = EngineThresholds.get_thresholds()
        self.severity_order = FaultPatterns.get_severity_order()
        self.maintenance_intervals = EngineThresholds.get_maintenance_intervals()
    
    def analyze_fault_codes(self, fault_codes: List[str]) -> Dict[str, Any]:
        """Analyze OBD fault codes"""
        if not fault_codes:
            return {"faults": [], "summary": "No fault codes detected"}
        
        faults = []
        systems_affected = set()
        max_severity = FaultSeverity.INFO
        immediate_action_needed = False
        
        for code in fault_codes:
            fault_info = self._get_fault_info(code)
            faults.append(fault_info)
            
            if fault_info.get("system"):
                systems_affected.add(fault_info["system"])
            
            # Track highest severity
            severity = fault_info.get("severity", FaultSeverity.INFO)
            if self.severity_order.get(severity, 0) > self.severity_order.get(max_severity, 0):
                max_severity = severity
            
            if fault_info.get("immediate_action"):
                immediate_action_needed = True
        
        return {
            "faults": faults,
            "systems_affected": list(systems_affected),
            "max_severity": max_severity.value,
            "immediate_action_needed": immediate_action_needed,
            "summary": self._generate_fault_summary(faults)
        }
    
    def _get_fault_info(self, code: str) -> Dict[str, Any]:
        """Get detailed information for a fault code"""
        if code in self.fault_patterns:
            pattern = self.fault_patterns[code]
            return {
                "code": code,
                "description": pattern["description"],
                "system": pattern["system"].value,
                "severity": pattern["severity"],
                "causes": pattern["causes"],
                "immediate_action": pattern.get("immediate_action", False)
            }
        
        # Handle unknown codes
        return {
            "code": code,
            "description": f"Unknown fault code: {code}",
            "system": SystemType.ENGINE.value,
            "severity": FaultSeverity.INFO,
            "causes": ["Requires professional diagnosis"],
            "immediate_action": False
        }
    
    def _generate_fault_summary(self, faults: List[Dict]) -> str:
        """Generate a summary of detected faults"""
        if not faults:
            return "No faults detected"
        
        critical_faults = [f for f in faults if f.get("severity") == FaultSeverity.CRITICAL]
        high_faults = [f for f in faults if f.get("severity") == FaultSeverity.HIGH]
        
        if critical_faults:
            return f"CRITICAL: {len(critical_faults)} critical fault(s) detected. Immediate service required!"
        elif high_faults:
            return f"WARNING: {len(high_faults)} high-priority fault(s) detected. Service recommended soon."
        else:
            return f"{len(faults)} fault(s) detected. Schedule routine maintenance."
    
    def generate_recommendations(self, parameters: Dict[str, Any], 
                               faults: List[Dict], 
                               mileage: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        # Fault-based recommendations
        for fault in faults:
            if fault.get("severity") in [FaultSeverity.CRITICAL, FaultSeverity.HIGH]:
                recommendations.append({
                    "type": "immediate",
                    "item": f"Address fault code {fault.get('code')}",
                    "description": fault.get("description", ""),
                    "priority": "high",
                    "estimated_cost": "$200-$800"
                })
        
        # Parameter-based recommendations
        if parameters:
            param_recommendations = self._analyze_parameters(parameters)
            recommendations.extend(param_recommendations)
        
        # Mileage-based recommendations
        if mileage:
            mileage_recommendations = self._get_mileage_recommendations(mileage)
            recommendations.extend(mileage_recommendations)
        
        # Remove duplicates and sort by priority
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = (rec["type"], rec["item"])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return sorted(unique_recommendations, 
                     key=lambda x: 0 if x.get("priority") == "high" else 1)
    
    def _analyze_parameters(self, parameters: Dict[str, Any]) -> List[Dict]:
        """Analyze vehicle parameters for issues"""
        recommendations = []
        engine_size = parameters.get("engine_size", "2.0L")
        thresholds = EngineThresholds.get_threshold_for_engine(engine_size)
        
        # Check coolant temperature
        coolant_temp = parameters.get("coolant_temp")
        if coolant_temp:
            normal_range = thresholds["coolant_temp_normal"]
            if coolant_temp < normal_range[0]:
                recommendations.append({
                    "type": "maintenance",
                    "item": "Check thermostat",
                    "description": "Coolant temperature below normal range",
                    "priority": "medium",
                    "estimated_cost": "$50-$150"
                })
            elif coolant_temp > normal_range[1]:
                recommendations.append({
                    "type": "immediate",
                    "item": "Check cooling system",
                    "description": "Engine overheating detected",
                    "priority": "high",
                    "estimated_cost": "$100-$500"
                })
        
        # Check oil pressure
        oil_pressure = parameters.get("oil_pressure")
        if oil_pressure and oil_pressure < thresholds["oil_pressure_min"]:
            recommendations.append({
                "type": "immediate",
                "item": "Check oil level and pressure",
                "description": "Low oil pressure detected",
                "priority": "high",
                "estimated_cost": "$50-$300"
            })
        
        return recommendations
    
    def _get_mileage_recommendations(self, mileage: int) -> List[Dict]:
        """Get maintenance recommendations based on mileage"""
        recommendations = []
        
        for item, interval in self.maintenance_intervals.items():
            if mileage % interval < 1000:  # Within 1000 miles of service interval
                item_name = item.replace("_", " ").title()
                recommendations.append({
                    "type": "scheduled",
                    "item": item_name,
                    "description": f"Due at {interval} mile intervals",
                    "priority": "medium",
                    "estimated_cost": self._get_maintenance_cost(item)
                })
        
        return recommendations
    
    def _get_maintenance_cost(self, item: str) -> str:
        """Get estimated maintenance cost"""
        costs = {
            "oil_change": "$30-$70",
            "air_filter": "$20-$40",
            "spark_plugs": "$100-$300",
            "coolant_flush": "$100-$150",
            "transmission_fluid": "$150-$250",
            "brake_fluid": "$70-$120",
            "power_steering_fluid": "$50-$100",
            "differential_fluid": "$80-$150",
            "fuel_filter": "$50-$100",
            "cabin_air_filter": "$20-$50"
        }
        return costs.get(item, "$50-$200")
