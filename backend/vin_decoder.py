"""
VIN Decoder Service with Public API Integration
Supports NHTSA and fallback local decoding
"""
import re
import random
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import aiohttp
from external_apis import NHTSAApi

logger = logging.getLogger(__name__)


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
    """VIN (Vehicle Identification Number) decoder service with NHTSA API integration"""

    def __init__(self, use_nhtsa_api: bool = True):
        self.valid_pattern = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')
        self.use_nhtsa_api = use_nhtsa_api
        self.nhtsa_api = NHTSAApi() if use_nhtsa_api else None
        # Mock database of vehicle information (fallback)
        self.vehicle_db = self._init_vehicle_db()

    def validate(self, vin: str) -> bool:
        """Validate VIN format"""
        if len(vin) != 17:
            return False
        # VIN should not contain I, O, or Q
        if re.search(r'[IOQ]', vin.upper()):
            return False
        return bool(self.valid_pattern.match(vin.upper()))

    def decode(self, vin: str) -> Dict[str, Any]:
        """Decode a VIN and return vehicle information"""
        if not self.validate(vin):
            raise ValueError(f"Invalid VIN: {vin}")

        # Try NHTSA API first if enabled
        if self.use_nhtsa_api and self.nhtsa_api:
            try:
                # Run async code in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    vehicle_info = loop.run_until_complete(self.nhtsa_api.decode_vin(vin))
                    
                    if vehicle_info and vehicle_info.get("make"):
                        logger.info(f"Successfully decoded VIN {vin} using NHTSA API")
                        return {
                            "vin": vin,
                            "valid": True,
                            "source": "nhtsa",
                            **vehicle_info
                        }
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(f"NHTSA API failed for VIN {vin}, using fallback: {e}")
        
        # Fallback to local decode
        logger.info(f"Using local decode for VIN {vin}")
        
        # Extract information from VIN
        wmi = vin[:3]  # World Manufacturer Identifier
        vds = vin[3:9]  # Vehicle Descriptor Section
        vis = vin[9:]  # Vehicle Identifier Section

        # Mock decode - in production, this would query real databases
        # For demo, return realistic data based on VIN patterns
        vehicle_info = self._lookup_vehicle(vin)

        return {
            "vin": vin,
            "valid": True,
            "wmi": wmi,
            "vds": vds,
            "vis": vis,
            "source": "local",
            **vehicle_info
        }

    def _lookup_vehicle(self, vin: str) -> Dict[str, Any]:
        """Look up vehicle information from VIN patterns"""
        # WMI (World Manufacturer Identifier) - positions 1-3
        wmi = vin[:3]
        
        # VDS (Vehicle Descriptor Section) - positions 4-9
        vds = vin[3:9]
        
        # Year decoding (position 10)
        year = self._decode_year(vin[9])
        
        # Get manufacturer info
        make_info = self._decode_manufacturer(wmi)
        make = make_info[0]
        model = self._infer_model(wmi, vds)
        
        # Engine and other details (would require full database)
        engine_map = {
            'A': 1.4, 'B': 1.6, 'C': 1.8, 'D': 2.0,
            'F': 2.4, 'G': 2.5, 'H': 3.0, 'J': 3.5,
            'K': 4.0, 'L': 5.0, 'M': 6.2
        }
        engine_code = vds[1] if len(vds) > 1 else 'D'
        engine_size = engine_map.get(engine_code, 2.0)
        
        return {
            "make": make,
            "model": model,
            "year": year,
            "body_type": self._get_body_type(vds),
            "engine_size": engine_size,
            "engine_cylinders": self._estimate_cylinders(engine_size),
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "drive_type": "FWD",
            "doors": 4,
            "manufacturer": make_info[0],
            "plant_country": make_info[1],
            "plant_city": "Unknown",
            "vehicle_type": "PASSENGER CAR"
        }

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
        return year_map.get(year_code, 2020)

    def _decode_manufacturer(self, wmi: str):
        """Decode manufacturer from WMI"""
        manufacturer_map = {
            "1HG": ("Honda", "USA"),
            "2HG": ("Honda", "Canada"),
            "JHM": ("Honda", "Japan"),
            "1G": ("General Motors", "USA"),
            "1F": ("Ford", "USA"),
            "WBA": ("BMW", "Germany"),
            "WDB": ("Mercedes-Benz", "Germany"),
            "WAU": ("Audi", "Germany"),
            "JT": ("Toyota", "Japan"),
            "5YJ": ("Tesla", "USA"),
            "KM": ("Hyundai", "South Korea"),
            "19X": ("Acura", "USA")
        }
        
        # Check exact match first
        if wmi in manufacturer_map:
            return manufacturer_map[wmi]
        
        # Check prefix match
        for prefix, info in manufacturer_map.items():
            if wmi.startswith(prefix[:2]):
                return info
        
        return ("Unknown", "Unknown")

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

    def _get_body_type(self, vds: str) -> str:
        """Determine body type from VDS"""
        # This is simplified - actual logic would be more complex
        body_codes = {
            'S': 'Sedan',
            'C': 'Coupe',
            'H': 'Hatchback',
            'W': 'Wagon',
            'V': 'SUV',
            'T': 'Truck',
            'M': 'Minivan'
        }
        
        if len(vds) > 2:
            return body_codes.get(vds[2], 'Sedan')
        return 'Sedan'

    def _estimate_cylinders(self, engine_size: float) -> int:
        """Estimate cylinder count from engine size"""
        if engine_size <= 1.5:
            return 3
        elif engine_size <= 2.5:
            return 4
        elif engine_size <= 4.0:
            return 6
        else:
            return 8

    def get_recalls(self, vin: str) -> list:
        """Get recall information for a vehicle"""
        # Try NHTSA API first if enabled
        if self.use_nhtsa_api and self.nhtsa_api:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    recalls = loop.run_until_complete(self.nhtsa_api.get_recall_info(vin))
                    if recalls:
                        logger.info(f"Found {len(recalls)} recalls for VIN {vin} from NHTSA")
                        return recalls
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(f"NHTSA recall API failed for VIN {vin}: {e}")
        
        # Fallback to mock recall data
        logger.info(f"Using mock recalls for VIN {vin}")
        recalls = [
            {
                "campaign_number": "23V456",
                "component": "FUEL SYSTEM",
                "summary": "Fuel pump may fail causing engine stall",
                "remedy": "Replace fuel pump module",
                "risk": "high"
            },
            {
                "campaign_number": "22V789",
                "component": "AIRBAGS",
                "summary": "Side airbag may not deploy properly",
                "remedy": "Update airbag control module software",
                "risk": "moderate"
            }
        ]

        # Randomly return 0-2 recalls
        num_recalls = random.randint(0, 2)
        return recalls[:num_recalls]

    def _init_vehicle_db(self):
        """Initialize mock vehicle database for testing"""
        return {
            "1HGCM82633A005007": {
                "make": "Honda",
                "model": "Civic",
                "year": 2003,
                "body_type": "Sedan",
                "engine_size": 1.7,
                "engine_cylinders": 4,
                "fuel_type": "Gasoline",
                "transmission": "Manual",
                "drive_type": "FWD",
                "doors": 4
            },
            # Add more vehicles to the mock database as needed
        }

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
