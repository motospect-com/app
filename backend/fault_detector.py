"""
Fault Detection System for vehicles up to 3L engine capacity
Analyzes OBD parameters and detects common fault patterns
"""

from typing import Dict, List, Any, Optional
from fault_patterns import FaultSeverity, SystemType, FaultPatterns
from engine_thresholds import EngineThresholds
from fault_analyzer import FaultAnalyzer
from health_calculator import HealthCalculator


class FaultDetector:
    """
    Advanced fault detection for vehicles with engines up to 3L capacity
    """

    def __init__(self):
        self.analyzer = FaultAnalyzer()
        self.health_calculator = HealthCalculator()
        self.engine_thresholds = EngineThresholds.get_thresholds()
        self.fault_patterns = FaultPatterns.get_patterns()
    
    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def analyze_fault_codes(self, codes):
        """Analyze OBD fault codes"""
        return self.analyzer.analyze_fault_codes(codes)

    def calculate_health_scores(self, parameters, codes):
        """Calculate health scores for vehicle systems"""
        analysis = self.analyzer.analyze_fault_codes(codes)
        faults = analysis.get("faults", []) if isinstance(analysis, dict) else analysis
        return self.health_calculator.calculate_health_scores(faults, parameters)
    
    def generate_recommendations(self, parameters: Dict[str, Any], 
                               fault_codes: List[str], 
                               mileage: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate maintenance recommendations"""
        analysis = self.analyzer.analyze_fault_codes(fault_codes)
        faults = analysis.get("faults", [])
        return self.analyzer.generate_recommendations(parameters, faults, mileage)
    
    def analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical trends for predictive maintenance"""
        return self.health_calculator.analyze_trends(historical_data)
    
    def analyze_parameters(self, 
                          parameters: Dict[str, Any],
                          engine_size: str = "2.0L") -> Dict[str, Any]:
        """
        Analyze OBD parameters and detect faults
        
        Args:
            parameters: OBD parameter readings
            engine_size: Engine displacement (e.g., "2.0L")
            
        Returns:
            Analysis results with detected issues
        """
        thresholds = EngineThresholds.get_threshold_for_engine(engine_size)
        issues = []
        
        # Check RPM
        rpm = parameters.get("rpm")
        if rpm:
            if rpm > thresholds["rpm_max"]:
                issues.append({
                    "parameter": "rpm",
                    "value": rpm,
                    "issue": "RPM exceeds maximum safe limit",
                    "severity": "high"
                })
        
        # Check coolant temperature
        coolant_temp = parameters.get("coolant_temp")
        if coolant_temp:
            normal_range = thresholds["coolant_temp_normal"]
            if coolant_temp > normal_range[1]:
                issues.append({
                    "parameter": "coolant_temp",
                    "value": coolant_temp,
                    "issue": "Engine overheating detected",
                    "severity": "critical"
                })
            elif coolant_temp < normal_range[0]:
                issues.append({
                    "parameter": "coolant_temp",
                    "value": coolant_temp,
                    "issue": "Engine running cold",
                    "severity": "low"
                })
        
        # Check oil pressure
        oil_pressure = parameters.get("oil_pressure")
        if oil_pressure and oil_pressure < thresholds["oil_pressure_min"]:
            issues.append({
                "parameter": "oil_pressure",
                "value": oil_pressure,
                "issue": "Low oil pressure detected",
                "severity": "critical"
            })
        
        return {
            "engine_size": engine_size,
            "issues": issues,
            "total_issues": len(issues),
            "status": "critical" if any(i["severity"] == "critical" for i in issues) else 
                     "warning" if issues else "normal"
        }
    
    def detect_misfires(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect engine misfires from parameter patterns"""
        misfire_data = []
        
        # Check for irregular RPM patterns
        rpm_history = parameters.get("rpm_history", [])
        if len(rpm_history) > 5:
            variations = [abs(rpm_history[i] - rpm_history[i-1]) for i in range(1, len(rpm_history))]
            avg_variation = sum(variations) / len(variations)
            
            if avg_variation > 100:  # Significant RPM variation
                misfire_data.append({
                    "type": "irregular_rpm",
                    "severity": "moderate",
                    "description": "Irregular RPM patterns detected"
                })
        
        return {
            "misfires_detected": len(misfire_data) > 0,
            "misfire_data": misfire_data,
            "severity": max([m["severity"] for m in misfire_data], default="none")
        }
    
    # ------------------------------------------------------------------
    # Legacy methods for backward compatibility
    # ------------------------------------------------------------------
    def _analyze_fault_codes(self, codes):
        """Legacy method - delegates to analyzer"""
        return self.analyzer.analyze_fault_codes(codes)

    def _calculate_health_scores(self, faults, parameters):
        """Legacy method - delegates to health calculator"""
        return self.health_calculator.calculate_health_scores(faults, parameters)
