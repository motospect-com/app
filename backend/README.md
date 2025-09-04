# MotoSpect Backend Service

## Overview
Core diagnostic service for vehicle fault detection supporting cars, vans, and SUVs with engines up to 3L capacity.

## Features
- **Vehicle Database Integration**: NHTSA VIN decoder and vehicle information lookup
- **Fault Detection System**: Advanced fault analysis for engines 1.0L to 3.0L
- **Multi-Sensor Support**: OBD, Audio, Thermal, and Time-of-Flight sensors
- **MQTT Integration**: Real-time sensor data ingestion via MQTT broker
- **Report Generation**: Comprehensive diagnostic reports with health scores
- **Predictive Analysis**: Failure prediction based on historical patterns

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /api/status` - System status

### Vehicle Information
- `GET /api/vin/{vin}` - Decode VIN
- `GET /api/vehicle/database/{vin}` - Get vehicle database info
- `GET /api/vehicle/maintenance` - Get maintenance schedule
- `GET /api/vehicle/common-problems` - Get common problems

### Diagnostic Scanning
- `POST /api/scan/start` - Start diagnostic scan
- `POST /api/scan/{scan_id}/stop` - Stop scan
- `GET /api/scan/{scan_id}/status` - Get scan status
- `GET /api/obd/auto-detect` - Auto-detect OBD connection

### Reporting
- `POST /api/report/generate` - Generate diagnostic report
- `GET /api/report/{report_id}` - Get report by ID
- `GET /api/report/{report_id}/pdf` - Download PDF report

### MQTT Channels
- `motospect/v1/obd` - OBD parameter data
- `motospect/v1/audio` - Audio spectrum analysis
- `motospect/v1/thermal` - Thermal imaging data
- `motospect/v1/tof` - Time-of-flight measurements

## Supported Vehicle Types
- Cars (Sedans, Hatchbacks, Coupes)
- SUVs (Compact, Mid-size, Full-size)
- Vans (Minivans, Cargo vans)
- Crossovers
- Light trucks (up to 3L engine)

## Engine Size Coverage
- **1.0L - 1.4L**: Small displacement engines
- **1.5L - 1.9L**: Compact engines
- **2.0L - 2.4L**: Mid-size engines
- **2.5L - 3.0L**: Large displacement engines

## Fault Detection Capabilities
- Engine misfires (P0300-P0308)
- Fuel system issues (P0171, P0174)
- Emission problems (P0420, P0430)
- Cooling system faults (P0128, P0125)
- Transmission issues
- Brake system monitoring
- Suspension analysis
- Electrical system diagnosis

## Configuration
Environment variables in `.env`:
```
BACKEND_PORT=8000
MQTT_BROKER_HOST=mosquitto
ENABLE_VEHICLE_DB=true
MAX_ENGINE_SIZE_L=3.0
FAULT_DETECTION_SENSITIVITY=medium
```

## Running Locally
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run service
python3 main.py
```

## Testing
```bash
# Run unit tests
python3 -m pytest -v

# Test vehicle database
python3 test_vehicle_database.py

# Test fault detection
python3 test_fault_detector.py
```

## Dependencies
- FastAPI - Web framework
- Pydantic - Data validation
- MQTT (Paho) - MQTT client
- NumPy - Numerical computations
- Requests - HTTP client
- Python 3.8+
