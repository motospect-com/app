# MOTOSPECT Project Structure

## Overview
The MOTOSPECT project has been refactored for better organization, reusability, and maintainability. The project supports both Docker Compose and microservices architectures.

## Directory Structure

```
motospect-com/app/
├── ansible/                 # Ansible playbooks for deployment
├── backend/                 # Main backend service
│   ├── main.py             # FastAPI application
│   ├── vin_decoder.py      # VIN decoding with NHTSA API
│   ├── fault_detector.py   # Fault detection system
│   └── external_apis.py    # External API integrations
├── customer-portal/         # React customer portal
├── frontend/               # Main React frontend
├── report-service/         # Report generation service
├── firmware/               # IoT firmware components
├── infrastructure/         # Infrastructure code
│   ├── service_manager.py  # Dynamic service management
│   ├── mqtt_service_bus.py # MQTT communication
│   └── testing_framework.py # Service testing framework
├── lib/                    # Shared libraries
│   ├── python/            
│   │   └── motospect/     # Python shared library
│   │       ├── __init__.py
│   │       ├── base_service.py  # Base microservice class
│   │       ├── config.py        # Configuration management
│   │       ├── health.py        # Health check utilities
│   │       └── logger.py        # Centralized logging
│   └── js/                # JavaScript shared libraries
├── mosquitto/             # MQTT broker configuration
├── scripts/               # All scripts organized by purpose
│   ├── docker/           # Docker-related scripts
│   │   ├── start.sh
│   │   ├── start_services.sh
│   │   ├── run_tests.sh
│   │   └── run_e2e_tests.sh
│   ├── microservices/    # Microservice management
│   │   ├── start_simple_microservices.sh
│   │   ├── stop_simple_microservices.sh
│   │   ├── start_microservices.sh
│   │   └── stop_microservices.sh
│   ├── testing/          # Test scripts and files
│   │   ├── test_all_services.py
│   │   ├── test_services_polish.py
│   │   ├── test_complete_system.py
│   │   ├── test_api_cors.py
│   │   └── test_microservices.py
│   ├── utils/            # Utility scripts
│   │   ├── diagnose.py
│   │   ├── demo_microservices.py
│   │   ├── quick_start.py
│   │   └── verify_microservices.py
│   └── env.sh           # Common environment setup
├── services/             # Microservices
│   ├── api-gateway/
│   ├── vin-decoder-service/
│   ├── fault-detector-service/
│   ├── diagnostic-service/
│   └── mqtt-bridge-service/
├── tests/                # Integration tests
├── docker-compose.yml    # Production Docker Compose
├── docker-compose.dev.yml # Development Docker Compose
├── Makefile             # Unified command interface
└── .env                 # Environment configuration

```

## Key Components

### 1. Shared Python Library (`lib/python/motospect/`)
Reusable Python components for all services:
- **BaseService**: Base class for creating microservices with FastAPI
- **HealthChecker**: Centralized health checking
- **Logger**: Unified logging configuration
- **Config**: Environment and configuration management

### 2. Scripts Organization (`scripts/`)
All scripts organized by purpose:
- **docker/**: Docker container management
- **microservices/**: Microservice lifecycle management
- **testing/**: Test execution scripts
- **utils/**: Utility and diagnostic scripts
- **env.sh**: Common environment setup for all scripts

### 3. Services Architecture
Two deployment modes:

#### Docker Compose Mode
- Full containerized deployment
- Uses `docker-compose.yml` for production
- Uses `docker-compose.dev.yml` for development
- Includes: backend, frontend, customer-portal, report-service, mosquitto

#### Microservices Mode
- Lightweight Python services
- Dynamic port allocation
- Service discovery via Service Manager
- Services: api-gateway, vin-decoder, fault-detector, diagnostic, mqtt-bridge

## Usage

### Quick Start
```bash
# Using Makefile (recommended)
make quick-start          # Quick start without Docker
make up                   # Start with Docker Compose
make up-dev              # Start in development mode
make start-microservices # Start microservices

# Direct script execution
bash scripts/docker/start.sh
bash scripts/microservices/start_simple_microservices.sh
```

### Testing
```bash
# Comprehensive testing
make test-all            # Run all tests
make test-microservices  # Test microservices
make test-api           # Test API endpoints
make test-e2e           # End-to-end tests

# Direct test execution
python scripts/testing/test_all_services.py
```

### Service Management
```bash
# Status and monitoring
make status             # Check service status
make health-check       # Health check all services
make diagnose          # Run diagnostics

# Microservice control
make restart-microservices
make stop-microservices
```

## Environment Variables

Key environment variables (defined in `.env`):
```bash
# Service Ports
BACKEND_PORT=8030
FRONTEND_PORT=3030
CUSTOMER_PORTAL_PORT=3040
MQTT_PORT=1884

# Microservice Ports
API_GATEWAY_PORT=8000
VIN_DECODER_PORT=8001
FAULT_DETECTOR_PORT=8002
DIAGNOSTIC_PORT=8003
MQTT_BRIDGE_PORT=8004

# API Configuration
NHTSA_API_ENABLED=true
NHTSA_API_URL=https://vpic.nhtsa.dot.gov/api
```

## Development Workflow

1. **Local Development**:
   ```bash
   make dev-start          # Start development environment
   make test-all          # Run tests
   make logs             # View logs
   ```

2. **Microservices Development**:
   ```bash
   make start-microservices
   make test-microservices
   make restart-microservices
   ```

3. **Production Deployment**:
   ```bash
   make build            # Build images
   make up              # Deploy
   make status          # Verify
   ```

## Benefits of Refactored Structure

1. **Clear Organization**: Scripts, tests, and libraries organized by purpose
2. **Reusable Components**: Shared libraries reduce code duplication
3. **Flexible Deployment**: Support for both Docker and microservices
4. **Unified Interface**: Makefile provides consistent command interface
5. **Better Testing**: Organized test suites with clear separation
6. **Environment Management**: Centralized configuration via env.sh
7. **Maintainability**: Clear structure makes it easier to navigate and modify

## Migration Notes

- All bash scripts moved to `scripts/` directory
- Test files moved to `scripts/testing/`
- Utility scripts moved to `scripts/utils/`
- Shared Python code extracted to `lib/python/motospect/`
- Makefile updated to use organized script paths
- Both docker-compose files remain compatible
