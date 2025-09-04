"""
Fault Detection System for vehicles up to 3L engine capacity
Analyzes OBD parameters and detects common fault patterns
"""

from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import numpy as np


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


class FaultDetector:
    """
    Advanced fault detection for vehicles with engines up to 3L capacity
    """
    
    def __init__(self):
        # Parameter thresholds for different engine sizes
        self.engine_thresholds = {
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
        
        # Common fault patterns
        self.fault_patterns = {
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
            }
        }
    
    def analyze_parameters(self, 
                          parameters: Dict[str, Any],
                          engine_size: str = "2.0L") -> Dict[str, Any]:
        """
        Analyze OBD parameters and detect faults
        
        Args:
            parameters: OBD parameter readings
            engine_size: Engine displacement (e.g., "2.0L")
            
        Returns:
            Analysis results with detected faults and recommendations
        """
        faults = []
        warnings = []
        recommendations = []
        
        # Get thresholds for engine size
        thresholds = self._get_engine_thresholds(engine_size)
        
        # Check engine parameters
        if "rpm" in parameters:
            rpm_faults = self._check_rpm(parameters["rpm"], thresholds)
            faults.extend(rpm_faults)
        
        if "coolant_temp" in parameters:
            temp_faults = self._check_coolant_temp(
                parameters["coolant_temp"], thresholds
            )
            faults.extend(temp_faults)
        
        if "oil_pressure" in parameters:
            oil_faults = self._check_oil_pressure(
                parameters["oil_pressure"], 
                parameters.get("rpm", 800),
                thresholds
            )
            faults.extend(oil_faults)
        
        if "fuel_pressure" in parameters:
            fuel_faults = self._check_fuel_pressure(
                parameters["fuel_pressure"], thresholds
            )
            faults.extend(fuel_faults)
        
        # Check for misfire patterns
        if "misfire_count" in parameters:
            misfire_faults = self._check_misfire(
                parameters["misfire_count"],
                parameters.get("cylinder_count", 4)
            )
            faults.extend(misfire_faults)
        
        # Analyze fault codes
        if "fault_codes" in parameters:
            code_analysis = self._analyze_fault_codes(
                parameters["fault_codes"]
            )
            faults.extend(code_analysis["faults"])
            recommendations.extend(code_analysis["recommendations"])
        
        # Calculate system health scores
        health_scores = self._calculate_health_scores(
            faults, parameters
        )
        
        # Generate recommendations based on faults
        recommendations.extend(
            self._generate_recommendations(faults, parameters)
        )
        
        return {
            "faults": faults,
            "warnings": warnings,
            "recommendations": recommendations,
            "health_scores": health_scores,
            "overall_health": self._calculate_overall_health(health_scores),
            "immediate_attention": any(
                f.get("immediate_action", False) for f in faults
            )
        }
    
    def _get_engine_thresholds(self, engine_size: str) -> Dict[str, Any]:
        """Get thresholds based on engine size"""
        # Find closest match
        if engine_size in self.engine_thresholds:
            return self.engine_thresholds[engine_size]
        
        # Extract numeric value
        try:
            size = float(engine_size.replace("L", ""))
            # Find closest available threshold
            available = [1.0, 1.5, 2.0, 2.5, 3.0]
            closest = min(available, key=lambda x: abs(x - size))
            return self.engine_thresholds[f"{closest}L"]
        except:
            return self.engine_thresholds["2.0L"]  # Default
    
    def _check_rpm(self, rpm: float, 
                   thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check RPM for issues"""
        faults = []
        
        idle_min, idle_max = thresholds["rpm_idle"]
        
        # Check idle RPM (assuming idle if rpm < 1200)
        if rpm < 1200:
            if rpm < idle_min:
                faults.append({
                    "code": "LOW_IDLE_RPM",
                    "description": f"Idle RPM too low ({rpm} RPM)",
                    "severity": FaultSeverity.MODERATE,
                    "system": SystemType.ENGINE,
                    "value": rpm,
                    "threshold": f"{idle_min}-{idle_max}"
                })
            elif rpm > idle_max:
                faults.append({
                    "code": "HIGH_IDLE_RPM",
                    "description": f"Idle RPM too high ({rpm} RPM)",
                    "severity": FaultSeverity.MODERATE,
                    "system": SystemType.ENGINE,
                    "value": rpm,
                    "threshold": f"{idle_min}-{idle_max}"
                })
        
        # Check max RPM
        if rpm > thresholds["rpm_max"]:
            faults.append({
                "code": "OVER_REV",
                "description": f"Engine over-revving ({rpm} RPM)",
                "severity": FaultSeverity.HIGH,
                "system": SystemType.ENGINE,
                "value": rpm,
                "threshold": thresholds["rpm_max"],
                "immediate_action": True
            })
        
        return faults
    
    def _check_coolant_temp(self, temp: float,
                           thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check coolant temperature"""
        faults = []
        
        temp_min, temp_max = thresholds["coolant_temp_normal"]
        
        if temp < temp_min - 10:
            faults.append({
                "code": "LOW_COOLANT_TEMP",
                "description": f"Coolant temperature too low ({temp}°C)",
                "severity": FaultSeverity.LOW,
                "system": SystemType.COOLING,
                "value": temp,
                "threshold": f"{temp_min}-{temp_max}°C"
            })
        elif temp > temp_max:
            severity = (FaultSeverity.CRITICAL if temp > temp_max + 15 
                       else FaultSeverity.HIGH)
            faults.append({
                "code": "HIGH_COOLANT_TEMP",
                "description": f"Engine overheating ({temp}°C)",
                "severity": severity,
                "system": SystemType.COOLING,
                "value": temp,
                "threshold": f"{temp_min}-{temp_max}°C",
                "immediate_action": temp > temp_max + 10
            })
        
        return faults
    
    def _check_oil_pressure(self, pressure: float, rpm: float,
                           thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check oil pressure relative to RPM"""
        faults = []
        
        # Minimum pressure increases with RPM
        min_pressure = thresholds["oil_pressure_min"]
        if rpm > 2000:
            min_pressure = min_pressure * 1.5
        
        if pressure < min_pressure:
            severity = (FaultSeverity.CRITICAL if pressure < min_pressure * 0.5
                       else FaultSeverity.HIGH)
            faults.append({
                "code": "LOW_OIL_PRESSURE",
                "description": f"Low oil pressure ({pressure} PSI at {rpm} RPM)",
                "severity": severity,
                "system": SystemType.ENGINE,
                "value": pressure,
                "threshold": f">{min_pressure} PSI",
                "immediate_action": True
            })
        
        return faults
    
    def _check_fuel_pressure(self, pressure: float,
                           thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check fuel pressure"""
        faults = []
        
        pressure_min, pressure_max = thresholds["fuel_pressure"]
        
        if pressure < pressure_min:
            faults.append({
                "code": "LOW_FUEL_PRESSURE",
                "description": f"Low fuel pressure ({pressure} PSI)",
                "severity": FaultSeverity.MODERATE,
                "system": SystemType.FUEL,
                "value": pressure,
                "threshold": f"{pressure_min}-{pressure_max} PSI"
            })
        elif pressure > pressure_max:
            faults.append({
                "code": "HIGH_FUEL_PRESSURE",
                "description": f"High fuel pressure ({pressure} PSI)",
                "severity": FaultSeverity.MODERATE,
                "system": SystemType.FUEL,
                "value": pressure,
                "threshold": f"{pressure_min}-{pressure_max} PSI"
            })
        
        return faults
    
    def _check_misfire(self, misfire_count: Dict[str, int],
                      cylinder_count: int) -> List[Dict[str, Any]]:
        """Check for misfire patterns"""
        faults = []
        
        total_misfires = sum(misfire_count.values())
        
        if total_misfires > 0:
            # Check if random or specific cylinder
            cylinders_affected = [cyl for cyl, count in misfire_count.items() 
                                 if count > 0]
            
            if len(cylinders_affected) > cylinder_count / 2:
                faults.append({
                    "code": "P0300",
                    "description": "Random/Multiple Cylinder Misfire Detected",
                    "severity": FaultSeverity.HIGH,
                    "system": SystemType.ENGINE,
                    "value": total_misfires,
                    "cylinders": cylinders_affected,
                    "immediate_action": total_misfires > 100
                })
            else:
                for cylinder, count in misfire_count.items():
                    if count > 10:
                        faults.append({
                            "code": f"P030{cylinder}",
                            "description": f"Cylinder {cylinder} Misfire",
                            "severity": FaultSeverity.MODERATE,
                            "system": SystemType.ENGINE,
                            "value": count,
                            "cylinder": cylinder
                        })
        
        return faults
    
    def _analyze_fault_codes(self, 
                            codes: List[str]) -> Dict[str, List[Any]]:
        """Analyze OBD fault codes"""
        faults = []
        recommendations = []
        
        for code in codes:
            if code in self.fault_patterns:
                pattern = self.fault_patterns[code]
                faults.append({
                    "code": code,
                    "description": pattern["description"],
                    "severity": pattern["severity"],
                    "system": pattern["system"],
                    "causes": pattern["causes"],
                    "immediate_action": pattern.get("immediate_action", False)
                })
                
                # Generate recommendations
                for cause in pattern["causes"][:2]:  # Top 2 likely causes
                    recommendations.append({
                        "text": f"Check {cause.lower()} ({code})",
                        "priority": ("High" if pattern["severity"] in 
                                   [FaultSeverity.HIGH, FaultSeverity.CRITICAL]
                                   else "Medium"),
                        "system": pattern["system"].value
                    })
        
        return {"faults": faults, "recommendations": recommendations}
    
    def _calculate_health_scores(self, faults: List[Dict[str, Any]],
                                parameters: Dict[str, Any]) -> Dict[str, float]:
        """Calculate health scores for each system"""
        scores = {
            SystemType.ENGINE.value: 100,
            SystemType.TRANSMISSION.value: 100,
            SystemType.BRAKES.value: 100,
            SystemType.SUSPENSION.value: 100,
            SystemType.ELECTRICAL.value: 100,
            SystemType.EMISSIONS.value: 100,
            SystemType.COOLING.value: 100,
            SystemType.FUEL.value: 100
        }
        
        # Deduct points based on faults
        severity_deduction = {
            FaultSeverity.CRITICAL: 40,
            FaultSeverity.HIGH: 25,
            FaultSeverity.MODERATE: 15,
            FaultSeverity.LOW: 8,
            FaultSeverity.INFO: 3
        }
        
        for fault in faults:
            system = fault.get("system")
            if system:
                system_name = (system.value if isinstance(system, SystemType) 
                             else system)
                severity = fault.get("severity", FaultSeverity.LOW)
                if isinstance(severity, str):
                    severity = FaultSeverity(severity)
                
                deduction = severity_deduction.get(severity, 10)
                if system_name in scores:
                    scores[system_name] = max(0, scores[system_name] - deduction)
        
        # Additional scoring based on parameters
        if "brake_pad_thickness" in parameters:
            thickness = parameters["brake_pad_thickness"]
            if thickness < 3:  # mm
                scores[SystemType.BRAKES.value] = min(
                    scores[SystemType.BRAKES.value], 60
                )
            elif thickness < 5:
                scores[SystemType.BRAKES.value] = min(
                    scores[SystemType.BRAKES.value], 75
                )
        
        return scores
    
    def _calculate_overall_health(self, 
                                 health_scores: Dict[str, float]) -> float:
        """Calculate overall vehicle health"""
        # Weighted average based on system importance
        weights = {
            SystemType.ENGINE.value: 0.25,
            SystemType.TRANSMISSION.value: 0.15,
            SystemType.BRAKES.value: 0.20,
            SystemType.SUSPENSION.value: 0.10,
            SystemType.ELECTRICAL.value: 0.10,
            SystemType.EMISSIONS.value: 0.08,
            SystemType.COOLING.value: 0.07,
            SystemType.FUEL.value: 0.05
        }
        
        total = sum(
            health_scores.get(system, 100) * weight 
            for system, weight in weights.items()
        )
        
        return round(total, 1)
    
    def _generate_recommendations(self, faults: List[Dict[str, Any]],
                                 parameters: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        # Check maintenance intervals
        if "mileage" in parameters:
            mileage = parameters["mileage"]
            
            if mileage % 5000 < 500:  # Within 500 miles of interval
                recommendations.append({
                    "text": "Oil change recommended",
                    "priority": "Medium",
                    "cost": "$40-80",
                    "interval": "5,000 miles"
                })
            
            if mileage > 30000 and mileage % 30000 < 1000:
                recommendations.append({
                    "text": "Transmission fluid service",
                    "priority": "Low",
                    "cost": "$100-150",
                    "interval": "30,000 miles"
                })
            
            if mileage > 60000 and mileage % 60000 < 2000:
                recommendations.append({
                    "text": "Spark plug replacement",
                    "priority": "Medium",
                    "cost": "$150-300",
                    "interval": "60,000 miles"
                })
        
        # Add recommendations based on faults
        for fault in faults:
            if fault.get("severity") in [FaultSeverity.HIGH, FaultSeverity.CRITICAL]:
                if "immediate_action" in fault and fault["immediate_action"]:
                    recommendations.insert(0, {
                        "text": f"URGENT: {fault['description']}",
                        "priority": "Critical",
                        "cost": "Diagnostic required",
                        "action": "Immediate attention"
                    })
        
        return recommendations
    
    def predict_failures(self, 
                        historical_data: List[Dict[str, Any]],
                        current_parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Predict potential failures based on trends
        
        Args:
            historical_data: List of previous parameter readings
            current_parameters: Current OBD parameters
            
        Returns:
            List of predicted failures with probability
        """
        predictions = []
        
        if len(historical_data) < 3:
            return predictions
        
        # Analyze trends
        trends = self._analyze_trends(historical_data)
        
        # Check oil pressure trend
        if "oil_pressure" in trends:
            trend = trends["oil_pressure"]
            if trend["slope"] < -0.5:  # Declining pressure
                days_to_failure = abs(20 / trend["slope"])  # 20 PSI threshold
                predictions.append({
                    "component": "Oil pump/Oil system",
                    "probability": min(90, 100 - days_to_failure),
                    "timeframe": f"{int(days_to_failure)} days",
                    "severity": FaultSeverity.HIGH,
                    "prevention": "Check oil level and quality, inspect for leaks"
                })
        
        # Check coolant temperature variance
        if "coolant_temp" in trends:
            trend = trends["coolant_temp"]
            if trend["variance"] > 10:  # High variance
                predictions.append({
                    "component": "Thermostat/Cooling system",
                    "probability": 70,
                    "timeframe": "2-4 weeks",
                    "severity": FaultSeverity.MODERATE,
                    "prevention": "Check thermostat operation, coolant level"
                })
        
        return predictions
    
    def _analyze_trends(self, 
                       historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze parameter trends over time"""
        trends = {}
        
        # Extract parameter time series
        parameters = {}
        for data in historical_data:
            for key, value in data.items():
                if key not in parameters:
                    parameters[key] = []
                parameters[key].append(value)
        
        # Calculate trends
        for param, values in parameters.items():
            if all(isinstance(v, (int, float)) for v in values):
                values_array = np.array(values, dtype=float)
                x = np.arange(len(values))
                
                # Linear regression
                slope, intercept = np.polyfit(x, values_array, 1)
                
                trends[param] = {
                    "slope": slope,
                    "intercept": intercept,
                    "mean": np.mean(values_array),
                    "variance": np.var(values_array),
                    "min": np.min(values_array),
                    "max": np.max(values_array)
                }
        
        return trends
