#!/usr/bin/env python3
"""
Microservices Configuration for MOTOSPECT
Service definitions and startup configuration
"""
import os
from pathlib import Path

# Load .env file
def load_env_config():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

load_env_config()

# Base paths
BASE_PATH = Path(__file__).parent.parent
SERVICES_PATH = BASE_PATH

# Microservices configurations
MICROSERVICES_CONFIG = {
    "vin-decoder-service": {
        "name": "VIN Decoder Service",
        "command": ["python3", "main.py"],
        "working_dir": "services/vin-decoder-service",
        "port": int(os.getenv("VIN_DECODER_SERVICE_PORT", "8001")),
        "environment": {
            "PYTHONPATH": "../../backend:$PYTHONPATH"
        },
        "dependencies": []
    },
    
    "fault-detector-service": {
        "name": "Fault Detector Service",
        "command": ["python3", "main.py"],
        "working_dir": "services/fault-detector-service",
        "port": int(os.getenv("FAULT_DETECTOR_SERVICE_PORT", "8002")),
        "environment": {
            "PYTHONPATH": "../../backend:$PYTHONPATH"
        },
        "dependencies": []
    },
    
    "diagnostic-service": {
        "name": "Diagnostic Service",
        "command": ["python3", "main.py"],
        "working_dir": "services/diagnostic-service",
        "port": int(os.getenv("DIAGNOSTIC_SERVICE_PORT", "8003")),
        "environment": {
            "PYTHONPATH": "../../backend:$PYTHONPATH"
        },
        "dependencies": ["vin-decoder-service", "fault-detector-service"]
    },
    
    "mqtt-bridge-service": {
        "name": "MQTT Bridge Service",
        "command": ["python3", "main.py"],
        "working_dir": "services/mqtt-bridge-service",
        "port": int(os.getenv("MQTT_BRIDGE_SERVICE_PORT", "8004")),
        "environment": {
            "PYTHONPATH": "../../backend:$PYTHONPATH",
            "MQTT_BROKER_HOST": "localhost",
            "MQTT_BROKER_PORT": os.getenv("MQTT_PORT", "1884")
        },
        "dependencies": []
    },
    
    "api-gateway": {
        "name": "API Gateway",
        "command": ["python3", "main.py"],
        "working_dir": "services/api-gateway",
        "port": int(os.getenv("API_GATEWAY_PORT", "8000")),
        "environment": {
            "PYTHONPATH": "../../backend:$PYTHONPATH"
        },
        "dependencies": ["vin-decoder-service", "fault-detector-service", "diagnostic-service", "mqtt-bridge-service"]
    }
}

# Startup order (respecting dependencies)
STARTUP_ORDER = [
    "vin-decoder-service",
    "fault-detector-service",
    "mqtt-bridge-service",
    "diagnostic-service",
    "api-gateway"
]

def get_service_config(service_name: str) -> ServiceConfig:
    """Get configuration for specific service"""
    return MICROSERVICES_CONFIG.get(service_name)

def get_all_services() -> dict:
    """Get all service configurations"""
    return MICROSERVICES_CONFIG

def get_startup_order() -> list:
    """Get recommended startup order"""
    return STARTUP_ORDER
