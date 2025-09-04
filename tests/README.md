# MotoSpect Test Suite

## Overview
Comprehensive testing framework for MotoSpect vehicle diagnostic system.

## Test Coverage
- **E2E Tests**: Complete system workflow validation
- **MQTT Simulation**: Sensor data generation and testing
- **API Tests**: Backend endpoint verification
- **Vehicle Database**: VIN decoder and database integration
- **Fault Detection**: Engine size-specific fault analysis

## Test Scripts

### End-to-End Testing
```bash
# Run complete E2E test suite
./run_e2e_tests.sh

# Python-based E2E tests
python3 e2e_test_scenario.py
```

### MQTT Sensor Simulation
```bash
# Simulate all sensor channels for 60 seconds
python3 mqtt_sensor_simulator.py --duration 60 --scan-id test-001

# Single sensor publish
python3 mqtt_sensor_simulator.py --single --channel obd
```

### Quick System Check
```bash
# Fast API endpoint verification
python3 quick_test.py
```

### Vehicle Database Testing
```bash
python3 test_vehicle_db_direct.py
```

## Sensor Data Formats

### OBD Channel
```json
{
  "scan_id": "test-001",
  "channel": "obd",
  "parameters": {
    "rpm": 2500,
    "coolant_temp": 92,
    "oil_pressure": 45,
    "fuel_pressure": 380
  },
  "fault_codes": ["P0301", "P0171"]
}
```

### Audio Channel
```json
{
  "scan_id": "test-001", 
  "channel": "audio",
  "spectrum": [/* frequency data */],
  "anomalies": ["bearing_noise", "exhaust_leak"]
}
```

### Thermal Channel
```json
{
  "scan_id": "test-001",
  "channel": "thermal",
  "zones": {
    "engine": 95.2,
    "brakes_fl": 45.8,
    "exhaust": 120.5
  }
}
```

### TOF Channel
```json
{
  "scan_id": "test-001",
  "channel": "tof",
  "measurements": {
    "tire_tread_fl": 7.2,
    "brake_pad_fl": 8.5,
    "suspension_height": 145
  }
}
```

## Test Vehicles
- **VIN**: 1HGBH41JXMN109186
- **Make**: Honda
- **Model**: Accord
- **Year**: 2021
- **Engine**: 2.0L
- **Mileage**: 45,000

### 2020 Honda Civic
- **VIN**: 19XFC2F52LE000576
- **Make**: Honda
- **Model**: Civic
- **Year**: 2020
- **Engine**: 2.0L
- **Mileage**: 30,000

## Expected Results
- All API endpoints responsive
- MQTT broker accepting connections
- VIN decoder returning vehicle data
- Fault detection generating health scores
- Reports containing recommendations
- PDF generation successful
