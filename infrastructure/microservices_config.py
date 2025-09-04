#!/usr/bin/env python3
"""
Microservices Configuration for MOTOSPECT
Service definitions and startup configuration
"""
import os
from pathlib import Path
from infrastructure.service_manager import ServiceConfig

# Base paths
BASE_PATH = Path(__file__).parent.parent
SERVICES_PATH = BASE_PATH / "services"

# Microservices configurations
MICROSERVICES_CONFIG = {
    "vin-decoder-service": ServiceConfig(
        name="vin-decoder-service",
        command=["python", "main.py"],
        working_dir=str(SERVICES_PATH / "vin-decoder-service"),
        port=8001,
        health_endpoint="/health",
        environment={
            "PORT": "8001",
            "PYTHONPATH": str(BASE_PATH / "backend")
        },
        dependencies=[]
    ),
    
    "fault-detector-service": ServiceConfig(
        name="fault-detector-service", 
        command=["python", "main.py"],
        working_dir=str(SERVICES_PATH / "fault-detector-service"),
        port=8002,
        health_endpoint="/health",
        environment={
            "PORT": "8002",
            "PYTHONPATH": str(BASE_PATH / "backend")
        },
        dependencies=[]
    ),
    
    "diagnostic-service": ServiceConfig(
        name="diagnostic-service",
        command=["python", "main.py"],
        working_dir=str(SERVICES_PATH / "diagnostic-service"),
        port=8003,
        health_endpoint="/health", 
        environment={
            "PORT": "8003",
            "PYTHONPATH": str(BASE_PATH / "backend")
        },
        dependencies=["vin-decoder-service", "fault-detector-service"]
    ),
    
    "mqtt-bridge-service": ServiceConfig(
        name="mqtt-bridge-service",
        command=["python", "main.py"],
        working_dir=str(SERVICES_PATH / "mqtt-bridge-service"),
        port=8004,
        health_endpoint="/health",
        environment={
            "PORT": "8004",
            "MQTT_HOST": "localhost",
            "MQTT_PORT": "1883",
            "MQTT_USER": "motospect",
            "MQTT_PASSWORD": "motospect123"
        },
        dependencies=[]
    ),
    
    "api-gateway": ServiceConfig(
        name="api-gateway",
        command=["python", "main.py"],
        working_dir=str(SERVICES_PATH / "api-gateway"),
        port=8000,
        health_endpoint="/health",
        environment={
            "PORT": "8000"
        },
        dependencies=["vin-decoder-service", "fault-detector-service", "diagnostic-service", "mqtt-bridge-service"]
    )
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
