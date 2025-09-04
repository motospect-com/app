"""
External API integrations for MOTOSPECT
Includes NHTSA VIN decoder, Weather API, and OBD data services
"""
import aiohttp
import asyncio
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cachetools import TTLCache
import hashlib

logger = logging.getLogger(__name__)


class ExternalAPIManager:
    """Manager for all external API integrations"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self.nhtsa = NHTSAApi()
        self.weather = WeatherApi()
        self.obd_cloud = OBDCloudApi()
        
    async def get_vehicle_info(self, vin: str) -> Dict[str, Any]:
        """Get comprehensive vehicle information from all APIs"""
        tasks = [
            self.nhtsa.decode_vin(vin),
            self.nhtsa.get_recall_info(vin),
            self.obd_cloud.get_vehicle_specs(vin)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        vehicle_info = {
            "vin": vin,
            "nhtsa_decode": results[0] if not isinstance(results[0], Exception) else None,
            "recalls": results[1] if not isinstance(results[1], Exception) else [],
            "obd_specs": results[2] if not isinstance(results[2], Exception) else None,
            "timestamp": datetime.now().isoformat()
        }
        
        return vehicle_info
    
    async def get_environmental_conditions(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current environmental conditions for location"""
        return await self.weather.get_current_conditions(latitude, longitude)


class NHTSAApi:
    """NHTSA (National Highway Traffic Safety Administration) API client"""
    
    def __init__(self):
        self.base_url = "https://vpic.nhtsa.dot.gov/api"
        self.cache = TTLCache(maxsize=500, ttl=86400)  # Cache for 24 hours
        
    async def decode_vin(self, vin: str) -> Dict[str, Any]:
        """
        Decode VIN using NHTSA API
        https://vpic.nhtsa.dot.gov/api/
        """
        cache_key = f"vin_decode_{vin}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached VIN decode for {vin}")
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/vehicles/DecodeVin/{vin}?format=json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse NHTSA response
                        vehicle_info = self._parse_nhtsa_response(data)
                        
                        # Cache the result
                        self.cache[cache_key] = vehicle_info
                        
                        logger.info(f"Successfully decoded VIN {vin} via NHTSA API")
                        return vehicle_info
                    else:
                        logger.error(f"NHTSA API returned status {response.status}")
                        return self._get_fallback_decode(vin)
                        
        except asyncio.TimeoutError:
            logger.error("NHTSA API timeout")
            return self._get_fallback_decode(vin)
        except Exception as e:
            logger.error(f"Error decoding VIN via NHTSA: {e}")
            return self._get_fallback_decode(vin)
    
    def _parse_nhtsa_response(self, data: Dict) -> Dict[str, Any]:
        """Parse NHTSA API response into structured format"""
        results = data.get("Results", [])
        
        vehicle_info = {
            "make": None,
            "model": None,
            "year": None,
            "body_type": None,
            "engine": {},
            "transmission": {},
            "drivetrain": None,
            "fuel_type": None,
            "manufacturer": None,
            "plant": None,
            "safety": {},
            "specifications": {}
        }
        
        # Map NHTSA variables to our structure
        for item in results:
            variable = item.get("Variable", "")
            value = item.get("Value", "")
            
            if not value or value == "Not Applicable":
                continue
                
            # Basic info
            if variable == "Make":
                vehicle_info["make"] = value
            elif variable == "Model":
                vehicle_info["model"] = value
            elif variable == "Model Year":
                vehicle_info["year"] = int(value) if value.isdigit() else value
            elif variable == "Body Class":
                vehicle_info["body_type"] = value
            elif variable == "Manufacturer Name":
                vehicle_info["manufacturer"] = value
            elif variable == "Plant Company Name":
                vehicle_info["plant"] = value
                
            # Engine info
            elif variable == "Engine Number of Cylinders":
                vehicle_info["engine"]["cylinders"] = int(value) if value.isdigit() else value
            elif variable == "Displacement (L)":
                vehicle_info["engine"]["displacement_l"] = float(value) if value.replace('.', '').isdigit() else value
            elif variable == "Engine Model":
                vehicle_info["engine"]["model"] = value
            elif variable == "Engine Power (kW)":
                vehicle_info["engine"]["power_kw"] = float(value) if value.replace('.', '').isdigit() else value
            elif variable == "Turbo":
                vehicle_info["engine"]["turbo"] = value.lower() == "yes"
                
            # Transmission
            elif variable == "Transmission Style":
                vehicle_info["transmission"]["style"] = value
            elif variable == "Transmission Speeds":
                vehicle_info["transmission"]["speeds"] = value
                
            # Fuel and drivetrain
            elif variable == "Fuel Type - Primary":
                vehicle_info["fuel_type"] = value
            elif variable == "Drive Type":
                vehicle_info["drivetrain"] = value
                
            # Safety features
            elif "Air Bag" in variable or "ABS" in variable or "ESC" in variable:
                vehicle_info["safety"][variable] = value
                
            # Other specifications
            elif variable in ["GVWR", "Curb Weight", "Wheelbase", "Gross Vehicle Weight Rating"]:
                vehicle_info["specifications"][variable] = value
        
        return vehicle_info
    
    async def get_recall_info(self, vin: str) -> List[Dict[str, Any]]:
        """Get recall information for a VIN"""
        cache_key = f"recalls_{vin}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached recalls for {vin}")
            return self.cache[cache_key]
        
        try:
            # Get model year first
            vin_info = await self.decode_vin(vin)
            year = vin_info.get("year")
            make = vin_info.get("make")
            model = vin_info.get("model")
            
            if not all([year, make, model]):
                return []
            
            url = f"{self.base_url}/vehicles/GetRecallsByVehicle"
            params = {
                "make": make,
                "model": model,
                "modelYear": year,
                "format": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        recalls = self._parse_recall_response(data)
                        
                        # Cache the result
                        self.cache[cache_key] = recalls
                        
                        logger.info(f"Found {len(recalls)} recalls for {vin}")
                        return recalls
                    else:
                        logger.error(f"Recall API returned status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching recalls: {e}")
            return []
    
    def _parse_recall_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse recall response"""
        results = data.get("results", [])
        
        recalls = []
        for recall in results:
            recalls.append({
                "campaign_number": recall.get("NHTSACampaignNumber"),
                "manufacturer": recall.get("Manufacturer"),
                "component": recall.get("Component"),
                "summary": recall.get("Summary"),
                "consequence": recall.get("Consequence"),
                "remedy": recall.get("Remedy"),
                "notes": recall.get("Notes"),
                "date": recall.get("ReportReceivedDate")
            })
        
        return recalls
    
    def _get_fallback_decode(self, vin: str) -> Dict[str, Any]:
        """Fallback VIN decode when API is unavailable"""
        # Basic VIN structure decode
        wmi = vin[:3] if len(vin) >= 3 else ""
        vds = vin[3:9] if len(vin) >= 9 else ""
        vis = vin[9:] if len(vin) >= 9 else ""
        
        # Simple manufacturer lookup
        manufacturer_map = {
            "1HG": "Honda",
            "2HG": "Honda (Canada)",
            "1G": "General Motors",
            "1F": "Ford",
            "WBA": "BMW",
            "WDB": "Mercedes-Benz",
            "WAU": "Audi",
            "JT": "Toyota",
            "JH": "Honda",
            "KM": "Hyundai",
            "5YJ": "Tesla"
        }
        
        manufacturer = None
        for prefix, mfr in manufacturer_map.items():
            if vin.startswith(prefix):
                manufacturer = mfr
                break
        
        # Year decode (simplified)
        year_code = vin[9] if len(vin) > 9 else ""
        year_map = {
            'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020,
            'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024
        }
        year = year_map.get(year_code, 2020)
        
        return {
            "make": manufacturer,
            "model": "Unknown",
            "year": year,
            "vin": vin,
            "source": "fallback",
            "wmi": wmi,
            "vds": vds,
            "vis": vis
        }


class WeatherApi:
    """Weather API integration for environmental conditions"""
    
    def __init__(self):
        # Using OpenWeatherMap as an example - requires API key
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache = TTLCache(maxsize=100, ttl=600)  # Cache for 10 minutes
        
    async def get_current_conditions(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather conditions for location"""
        cache_key = f"weather_{latitude}_{longitude}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached weather for {latitude}, {longitude}")
            return self.cache[cache_key]
        
        if not self.api_key:
            logger.warning("Weather API key not configured, using simulated data")
            return self._get_simulated_weather()
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        conditions = self._parse_weather_response(data)
                        
                        # Cache the result
                        self.cache[cache_key] = conditions
                        
                        logger.info(f"Retrieved weather for {latitude}, {longitude}")
                        return conditions
                    else:
                        logger.error(f"Weather API returned status {response.status}")
                        return self._get_simulated_weather()
                        
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self._get_simulated_weather()
    
    def _parse_weather_response(self, data: Dict) -> Dict[str, Any]:
        """Parse weather API response"""
        return {
            "temperature": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "wind_direction": data.get("wind", {}).get("deg"),
            "visibility": data.get("visibility"),
            "conditions": data.get("weather", [{}])[0].get("main"),
            "description": data.get("weather", [{}])[0].get("description"),
            "location": data.get("name"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_simulated_weather(self) -> Dict[str, Any]:
        """Get simulated weather data when API is unavailable"""
        import random
        
        return {
            "temperature": round(20 + random.uniform(-10, 15), 1),
            "humidity": random.randint(30, 90),
            "pressure": random.randint(990, 1030),
            "wind_speed": round(random.uniform(0, 20), 1),
            "wind_direction": random.randint(0, 360),
            "visibility": random.randint(5000, 10000),
            "conditions": random.choice(["Clear", "Cloudy", "Rain", "Snow"]),
            "description": "Simulated weather conditions",
            "location": "Simulated",
            "timestamp": datetime.now().isoformat(),
            "source": "simulated"
        }


class OBDCloudApi:
    """OBD Cloud service for vehicle diagnostics data"""
    
    def __init__(self):
        self.api_key = os.getenv("OBD_CLOUD_API_KEY", "")
        self.base_url = "https://api.obdcloud.com/v1"  # Example URL
        self.cache = TTLCache(maxsize=200, ttl=1800)  # Cache for 30 minutes
        
    async def get_vehicle_specs(self, vin: str) -> Dict[str, Any]:
        """Get vehicle specifications from OBD database"""
        cache_key = f"obd_specs_{vin}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached OBD specs for {vin}")
            return self.cache[cache_key]
        
        if not self.api_key:
            logger.warning("OBD Cloud API key not configured, using simulated data")
            return self._get_simulated_specs(vin)
        
        try:
            url = f"{self.base_url}/vehicle/specs"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {"vin": vin}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache the result
                        self.cache[cache_key] = data
                        
                        logger.info(f"Retrieved OBD specs for {vin}")
                        return data
                    else:
                        logger.error(f"OBD API returned status {response.status}")
                        return self._get_simulated_specs(vin)
                        
        except Exception as e:
            logger.error(f"Error fetching OBD specs: {e}")
            return self._get_simulated_specs(vin)
    
    async def get_dtc_definitions(self, codes: List[str]) -> Dict[str, str]:
        """Get Diagnostic Trouble Code definitions"""
        definitions = {}
        
        # Common DTC definitions (would normally come from API)
        dtc_database = {
            "P0300": "Random/Multiple Cylinder Misfire Detected",
            "P0301": "Cylinder 1 Misfire Detected",
            "P0302": "Cylinder 2 Misfire Detected",
            "P0303": "Cylinder 3 Misfire Detected",
            "P0304": "Cylinder 4 Misfire Detected",
            "P0171": "System Too Lean (Bank 1)",
            "P0172": "System Too Rich (Bank 1)",
            "P0420": "Catalyst System Efficiency Below Threshold (Bank 1)",
            "P0442": "EVAP Emission Control System Leak Detected (Small Leak)",
            "P0455": "EVAP Emission Control System Leak Detected (Large Leak)",
            "P0128": "Coolant Thermostat Below Regulating Temperature",
            "P0133": "O2 Sensor Circuit Slow Response (Bank 1, Sensor 1)",
            "P0505": "Idle Air Control System",
            "P0401": "EGR Flow Insufficient",
            "P0402": "EGR Flow Excessive",
            "B0001": "Driver Frontal Stage 1 Deployment Control",
            "C0035": "Left Front Wheel Speed Sensor Circuit",
            "U0100": "Lost Communication With ECM/PCM"
        }
        
        for code in codes:
            if code in dtc_database:
                definitions[code] = dtc_database[code]
            else:
                # Try to determine type from prefix
                if code.startswith("P"):
                    definitions[code] = "Powertrain fault code"
                elif code.startswith("B"):
                    definitions[code] = "Body system fault code"
                elif code.startswith("C"):
                    definitions[code] = "Chassis system fault code"
                elif code.startswith("U"):
                    definitions[code] = "Network communication fault code"
                else:
                    definitions[code] = "Unknown fault code"
        
        return definitions
    
    def _get_simulated_specs(self, vin: str) -> Dict[str, Any]:
        """Get simulated OBD specifications"""
        import random
        
        engine_sizes = [1.0, 1.4, 1.6, 1.8, 2.0, 2.4, 2.5, 3.0, 3.5, 4.0, 5.0, 6.2]
        
        return {
            "vin": vin,
            "obd_protocol": random.choice(["ISO 9141-2", "ISO 14230-4", "ISO 15765-4", "SAE J1850"]),
            "engine": {
                "size": random.choice(engine_sizes),
                "cylinders": random.choice([3, 4, 6, 8]),
                "fuel_type": random.choice(["Gasoline", "Diesel", "Hybrid", "Electric"]),
                "configuration": random.choice(["Inline", "V", "Flat", "Rotary"])
            },
            "emissions": {
                "standard": random.choice(["Euro 6", "EPA Tier 3", "CARB LEV III"]),
                "co2_g_km": random.randint(90, 250)
            },
            "sensors": {
                "oxygen_sensors": random.randint(2, 4),
                "cam_sensors": random.randint(1, 2),
                "crank_sensor": True,
                "maf_sensor": random.choice([True, False]),
                "map_sensor": random.choice([True, False]),
                "throttle_position": True,
                "coolant_temp": True,
                "intake_temp": True
            },
            "capabilities": {
                "live_data": True,
                "freeze_frame": True,
                "readiness_monitors": True,
                "dtc_reading": True,
                "dtc_clearing": True
            },
            "source": "simulated",
            "timestamp": datetime.now().isoformat()
        }


# Factory function
def create_api_manager() -> ExternalAPIManager:
    """Create and return an API manager instance"""
    return ExternalAPIManager()
