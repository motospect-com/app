"""
VIN Decoder Service with Public API Integration
Supports NHTSA and fallback local decoding
"""
import aiohttp
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import re
import asyncio
import os
import logging

@dataclass
class VehicleData:
    """Comprehensive vehicle information"""
    vin: str
    make: str
    model: str
    year: int
    body_type: str
    engine_size: float  # liters
    engine_cylinders: int
    fuel_type: str
    transmission: str
    drive_type: str
    doors: int
    manufacturer: str
    plant_country: str
    plant_city: str
    vehicle_type: str
    gvwr: str  # Gross Vehicle Weight Rating
    trim_level: str
    series: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class VINDecoder:
    """VIN decoder with multiple data sources"""
    
    NHTSA_API = "https://vpic.nhtsa.dot.gov/api/vehicles"
    
    def __init__(self, timeout: float = 3.0):
        """Initialize VINDecoder.

        Args:
            timeout (float): Maximum seconds to wait for outbound HTTP requests.
        """
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = timeout
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def decode_vin(self, vin: str) -> Optional[VehicleData]:
        """Decode VIN using multiple sources"""
        # Validate VIN format
        if not self._validate_vin(vin):
            raise ValueError(f"Invalid VIN format: {vin}")
            
        # Try NHTSA API first
        vehicle_data = await self._decode_nhtsa(vin)
        
        # Fallback to local decoding if API fails
        if not vehicle_data:
            vehicle_data = self._decode_local(vin)
            
        return vehicle_data
        
    def _validate_vin(self, vin: str) -> bool:
        """Validate VIN format (17 characters, alphanumeric)"""
        if len(vin) != 17:
            return False
        # VIN should not contain I, O, or Q
        if re.search(r'[IOQ]', vin.upper()):
            return False
        return bool(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin.upper()))
        
    async def _decode_nhtsa(self, vin: str) -> Optional[VehicleData]:
        """Decode using NHTSA government API"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            
        try:
            url = f"{self.NHTSA_API}/DecodeVin/{vin}?format=json"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                results = data.get("Results", [])
                
                # Parse NHTSA response
                vehicle_info = {}
                for item in results:
                    if item.get("Value"):
                        vehicle_info[item["Variable"]] = item["Value"]
                
                # Map NHTSA fields to our data structure
                return VehicleData(
                    vin=vin,
                    make=vehicle_info.get("Make", "Unknown"),
                    model=vehicle_info.get("Model", "Unknown"),
                    year=int(vehicle_info.get("ModelYear", 0)),
                    body_type=vehicle_info.get("BodyClass", "Unknown"),
                    engine_size=self._parse_engine_size(
                        vehicle_info.get("DisplacementL", "0")
                    ),
                    engine_cylinders=int(vehicle_info.get("EngineCylinders", 0)),
                    fuel_type=vehicle_info.get("FuelTypePrimary", "Unknown"),
                    transmission=vehicle_info.get("TransmissionStyle", "Unknown"),
                    drive_type=vehicle_info.get("DriveType", "Unknown"),
                    doors=int(vehicle_info.get("Doors", 0)),
                    manufacturer=vehicle_info.get("Manufacturer", "Unknown"),
                    plant_country=vehicle_info.get("PlantCountry", "Unknown"),
                    plant_city=vehicle_info.get("PlantCity", "Unknown"),
                    vehicle_type=vehicle_info.get("VehicleType", "Unknown"),
                    gvwr=vehicle_info.get("GVWR", "Unknown"),
                    trim_level=vehicle_info.get("Trim", "Unknown"),
                    series=vehicle_info.get("Series", "Unknown"),
                )
        except Exception as e:
            print(f"[VIN Decoder] NHTSA API error: {e}")
            return None
            
    def _parse_engine_size(self, displacement_str: str) -> float:
        """Parse engine displacement string to float"""
        try:
            return float(displacement_str)
        except (ValueError, TypeError):
            return 0.0
            
    def _decode_local(self, vin: str) -> VehicleData:
        """Local VIN decoding as fallback"""
        # WMI (World Manufacturer Identifier) - positions 1-3
        wmi = vin[:3]
        
        # VDS (Vehicle Descriptor Section) - positions 4-9
        vds = vin[3:9]
        
        # VIS (Vehicle Identifier Section) - positions 10-17
        vis = vin[9:]
        
        # Year decoding (position 10)
        year = self._decode_year(vin[9])
        
        # Manufacturer mapping
        manufacturer_map = {
            "1HG": ("Honda", "USA"),
            "19X": ("Honda", "USA"),
            "JHM": ("Honda", "Japan"),
            "WBA": ("BMW", "Germany"),
            "5YJ": ("Tesla", "USA"),
            "WAU": ("Audi", "Germany"),
            "1VW": ("Volkswagen", "USA"),
            "WVW": ("Volkswagen", "Germany"),
            "1G1": ("Chevrolet", "USA"),
            "1FA": ("Ford", "USA"),
            "JM1": ("Mazda", "Japan"),
            "KNA": ("Kia", "South Korea"),
            "5NP": ("Hyundai", "USA"),
        }
        
        make_info = manufacturer_map.get(wmi, ("Unknown", "Unknown"))
        
        # Basic model inference (would need extensive database for accuracy)
        model = self._infer_model(wmi, vds)
        
        return VehicleData(
            vin=vin,
            make=make_info[0],
            model=model,
            year=year,
            body_type="Sedan",  # Default, would need VDS decoding
            engine_size=2.0,  # Default
            engine_cylinders=4,  # Default
            fuel_type="Gasoline",
            transmission="Automatic",
            drive_type="FWD",
            doors=4,
            manufacturer=make_info[0],
            plant_country=make_info[1],
            plant_city="Unknown",
            vehicle_type="PASSENGER CAR",
            gvwr="Unknown",
            trim_level="Base",
            series="Unknown",
        )
        
    def _decode_year(self, year_code: str) -> int:
        """Decode model year from VIN position 10"""
        year_map = {
            'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
            'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
            'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024,
            'S': 2025, 'T': 2026, 'V': 2027, 'W': 2028, 'X': 2029,
            'Y': 2030, '1': 2001, '2': 2002, '3': 2003, '4': 2004,
            '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
        }
        return year_map.get(year_code.upper(), 2020)
        
    def _infer_model(self, wmi: str, vds: str) -> str:
        """Infer model from WMI and VDS (simplified)"""
        # This would need a comprehensive database
        # Simplified examples:
        if wmi.startswith("1HG"):
            if "CV" in vds:
                return "Civic"
            elif "CM" in vds:
                return "Accord"
        elif wmi.startswith("19X"):
            if vds.startswith("FC"):
                return "Civic"
            elif vds.startswith("FA"):
                return "Accord"
        elif wmi.startswith("WBA"):
            if vds[0] in ["F", "G"]:
                return "3 Series"
            elif vds[0] in ["H", "K"]:
                return "5 Series"
        elif wmi.startswith("5YJ"):
            if vds[0] == "S":
                return "Model S"
            elif vds[0] == "3":
                return "Model 3"
        
        return "Unknown Model"

class VehicleImageService:
    """Service to fetch vehicle images from various sources"""
    
    def __init__(self, timeout: float = 3.0):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = timeout
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_vehicle_images(self, make: str, model: str, year: int) -> Dict[str, str]:
        """Get vehicle images from various sources"""
        # In production, would integrate with:
        # - Edmunds API
        # - CarFax API
        # - Manufacturer APIs
        # For now, return placeholder URLs
        
        base_url = "https://via.placeholder.com"
        
        return {
            "exterior_front": f"{base_url}/800x600?text={make}+{model}+Front",
            "exterior_rear": f"{base_url}/800x600?text={make}+{model}+Rear",
            "exterior_side": f"{base_url}/800x600?text={make}+{model}+Side",
            "interior": f"{base_url}/800x600?text={make}+{model}+Interior",
            "engine": f"{base_url}/800x600?text={make}+{model}+Engine",
            "undercarriage": f"{base_url}/800x600?text={make}+{model}+Undercarriage",
        }

class PartsDatabase:
    """Parts and pricing database integration"""
    
    def __init__(self, timeout: float = 3.0):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = timeout
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_parts_for_vehicle(self, vehicle_data: VehicleData) -> List[Dict]:
        """Get parts catalog for specific vehicle"""
        # In production would integrate with:
        # - RockAuto API
        # - PartsGeek API
        # - OEM parts databases
        
        # Simulated parts data
        common_parts = [
            {
                "part_number": "BRK-001",
                "name": "Brake Pads (Front)",
                "category": "Brakes",
                "price": 45.99,
                "labor_hours": 1.5,
                "labor_cost": 120.00,
            },
            {
                "part_number": "FLT-001",
                "name": "Engine Oil Filter",
                "category": "Engine",
                "price": 12.99,
                "labor_hours": 0.5,
                "labor_cost": 40.00,
            },
            {
                "part_number": "FLT-002",
                "name": "Air Filter",
                "category": "Engine",
                "price": 18.99,
                "labor_hours": 0.25,
                "labor_cost": 20.00,
            },
            {
                "part_number": "SPK-001",
                "name": "Spark Plugs (Set of 4)",
                "category": "Ignition",
                "price": 32.99,
                "labor_hours": 1.0,
                "labor_cost": 80.00,
            },
            {
                "part_number": "BAT-001",
                "name": "Battery",
                "category": "Electrical",
                "price": 125.99,
                "labor_hours": 0.5,
                "labor_cost": 40.00,
            },
        ]
        
        return common_parts
        
    async def get_repair_costs(self, fault_codes: List[str]) -> Dict[str, float]:
        """Estimate repair costs based on fault codes"""
        # Simplified cost estimation
        cost_map = {
            "P0171": 150.00,  # Lean condition - O2 sensor
            "P0300": 300.00,  # Misfire - spark plugs/coils
            "P0442": 100.00,  # EVAP leak - gas cap/hose
            "P0420": 800.00,  # Catalyst efficiency
            "P0301": 200.00,  # Cylinder 1 misfire
        }
        
        total_parts = 0
        total_labor = 0
        
        for code in fault_codes:
            if code in cost_map:
                total_parts += cost_map[code] * 0.6  # 60% parts
                total_labor += cost_map[code] * 0.4  # 40% labor
                
        return {
            "parts_cost": round(total_parts, 2),
            "labor_cost": round(total_labor, 2),
            "total_cost": round(total_parts + total_labor, 2),
        }
