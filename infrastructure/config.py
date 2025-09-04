#!/usr/bin/env python3
"""
Configuration management for MOTOSPECT microservices
Loads settings from .env file
"""
import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from .env file"""
    if env_path is None:
        # Look for .env in project root
        current_dir = Path(__file__).parent
        env_path = current_dir.parent / ".env"
    
    env_vars = {}
    
    if Path(env_path).exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    # Also set in os.environ if not already set
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()
    
    return env_vars


class Config:
    """Configuration class for MOTOSPECT microservices"""
    
    def __init__(self):
        # Load .env file
        load_env_file()
        
        # Microservices ports
        self.VIN_DECODER_SERVICE_PORT = int(os.getenv('VIN_DECODER_SERVICE_PORT', '8001'))
        self.FAULT_DETECTOR_SERVICE_PORT = int(os.getenv('FAULT_DETECTOR_SERVICE_PORT', '8002'))
        self.DIAGNOSTIC_SERVICE_PORT = int(os.getenv('DIAGNOSTIC_SERVICE_PORT', '8003'))
        self.MQTT_BRIDGE_SERVICE_PORT = int(os.getenv('MQTT_BRIDGE_SERVICE_PORT', '8004'))
        self.API_GATEWAY_PORT = int(os.getenv('API_GATEWAY_PORT', '8000'))
        
        # Legacy ports for compatibility
        self.FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '3030'))
        self.BACKEND_PORT = int(os.getenv('BACKEND_PORT', '8030'))
        self.CUSTOMER_PORTAL_PORT = int(os.getenv('CUSTOMER_PORTAL_PORT', '3040'))
        self.REPORT_SERVICE_PORT = int(os.getenv('REPORT_SERVICE_PORT', '3050'))
        self.MQTT_PORT = int(os.getenv('MQTT_PORT', '1884'))
        self.MQTT_WS_PORT = int(os.getenv('MQTT_WS_PORT', '9002'))
        
        # Backend configuration
        self.ENABLE_MQTT_BRIDGE = os.getenv('ENABLE_MQTT_BRIDGE', 'true').lower() == 'true'
        
        # Service URLs
        self.VIN_DECODER_URL = f"http://localhost:{self.VIN_DECODER_SERVICE_PORT}"
        self.FAULT_DETECTOR_URL = f"http://localhost:{self.FAULT_DETECTOR_SERVICE_PORT}"
        self.DIAGNOSTIC_SERVICE_URL = f"http://localhost:{self.DIAGNOSTIC_SERVICE_PORT}"
        self.MQTT_BRIDGE_URL = f"http://localhost:{self.MQTT_BRIDGE_SERVICE_PORT}"
    
    def get_service_port(self, service_name: str) -> int:
        """Get port for a specific service"""
        port_mapping = {
            'vin-decoder-service': self.VIN_DECODER_SERVICE_PORT,
            'fault-detector-service': self.FAULT_DETECTOR_SERVICE_PORT,
            'diagnostic-service': self.DIAGNOSTIC_SERVICE_PORT,
            'mqtt-bridge-service': self.MQTT_BRIDGE_SERVICE_PORT,
            'api-gateway': self.API_GATEWAY_PORT,
        }
        return port_mapping.get(service_name, 8000)
    
    def get_service_url(self, service_name: str) -> str:
        """Get URL for a specific service"""
        port = self.get_service_port(service_name)
        return f"http://localhost:{port}"


# Global config instance
config = Config()


# Convenience functions for microservices
def get_vin_decoder_port() -> int:
    """Get VIN Decoder Service port"""
    return config.VIN_DECODER_SERVICE_PORT


def get_fault_detector_port() -> int:
    """Get Fault Detector Service port"""
    return config.FAULT_DETECTOR_SERVICE_PORT


def get_diagnostic_service_port() -> int:
    """Get Diagnostic Service port"""
    return config.DIAGNOSTIC_SERVICE_PORT


def get_mqtt_bridge_port() -> int:
    """Get MQTT Bridge Service port"""
    return config.MQTT_BRIDGE_SERVICE_PORT


def get_api_gateway_port() -> int:
    """Get API Gateway port"""
    return config.API_GATEWAY_PORT
