# MotoSpect E2E Test Scenario Documentation

## Overview
This document describes the comprehensive end-to-end testing scenarios for the MotoSpect vehicle diagnostic system, covering both service technician and customer workflows.

## Test Configuration

### Environment Variables (.env)
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3030`
- Customer Portal: `http://localhost:3040`
- Report Service: `http://localhost:3050`
- MQTT Broker: `mosquitto:1883`
- Test VIN: `1HGBH41JXMN109186` (Honda Accord 2021)

### Test Components
1. **Backend API** - FastAPI service with vehicle database integration
2. **MQTT Bridge** - Real-time sensor data ingestion
3. **Frontend** - Service technician interface
4. **Customer Portal** - Customer-facing interface
5. **Report Service** - PDF report generation
6. **Firmware Simulator** - MQTT sensor data simulation

## Service Technician Workflow Tests

### Test 1: Vehicle Identification
- **Objective**: Verify VIN decoding and vehicle database lookup
- **Steps**:
  1. Call `/api/vin/{TEST_VIN}` to decode VIN
  2. Call `/api/vehicle/database/{TEST_VIN}` for comprehensive vehicle info
- **Expected**: Vehicle make/model/year decoded, recalls and safety ratings retrieved

### Test 2: Start Diagnostic Scan
- **Objective**: Initialize a new diagnostic scan session
- **Steps**:
  1. POST to `/api/scan/start` with vehicle_id
  2. Receive scan_id for tracking
- **Expected**: Unique scan_id generated, scan session active

### Test 3: OBD Auto-Detection
- **Objective**: Test automatic vehicle detection via OBD
- **Steps**:
  1. GET `/api/obd/auto-detect`
  2. Verify detected vehicle info
- **Expected**: Vehicle make/model detected from OBD

### Test 4: Sensor Data Collection
- **Objective**: Collect multi-channel sensor data via MQTT
- **Channels**:
  - **OBD**: Engine parameters, fault codes, freeze frame data
  - **Audio**: Frequency spectrum analysis, anomaly detection
  - **Thermal**: Temperature zones, hotspot detection
  - **TOF**: Tire tread depth, brake pad thickness, suspension height
- **Steps**:
  1. Connect to MQTT broker
  2. Publish sensor data to `motospect/v1/{channel}`
  3. Verify data reception at `/api/latest`
- **Expected**: All sensor data received and stored

### Test 5: Stop Scan
- **Objective**: Properly terminate scan session
- **Steps**:
  1. POST to `/api/scan/{scan_id}/stop`
- **Expected**: Scan marked as complete

### Test 6: Report Generation
- **Objective**: Generate comprehensive diagnostic report
- **Steps**:
  1. POST to `/api/report/generate` with:
     - Vehicle info (VIN, make, model, year, mileage)
     - OBD parameters
     - Fault codes
     - Scan type
  2. Receive diagnostic report with:
     - Health scores (overall and by system)
     - Fault analysis
     - Recommendations
     - Predictive maintenance
- **Expected**: Complete report with health scores and recommendations

### Test 7: Maintenance Schedule
- **Objective**: Retrieve vehicle-specific maintenance schedule
- **Steps**:
  1. GET `/api/vehicle/maintenance` with make/model/year/mileage
- **Expected**: List of maintenance items with intervals

## Customer Portal Workflow Tests

### Test 8: Customer Portal Access
- **Objective**: Verify customer portal availability
- **Steps**:
  1. GET customer portal homepage
- **Expected**: Portal accessible at configured URL

### Test 9: Gate Simulation
- **Objective**: Simulate automated scanning gate
- **Steps**:
  1. POST `/api/gate/enter` with VIN
  2. Automatic scan initiation
- **Expected**: Scan started automatically when vehicle enters

### Test 10: Scan Status Check
- **Objective**: Customer checks scan progress
- **Steps**:
  1. GET `/api/scan/{scan_id}/status`
- **Expected**: Current scan status and progress

### Test 11: Common Problems
- **Objective**: Retrieve known issues for vehicle
- **Steps**:
  1. GET `/api/vehicle/common-problems` with vehicle details
- **Expected**: List of common problems with severity ratings

### Test 12: Report Download
- **Objective**: Download PDF diagnostic report
- **Steps**:
  1. GET `/api/report/{scan_id}/pdf`
- **Expected**: PDF report downloaded

## MQTT Sensor Simulation

### Simulated Data Types

#### OBD Data
```json
{
  "scan_id": "test-001",
  "channel": "obd",
  "vin": "1HGBH41JXMN109186",
  "parameters": {
    "rpm": 2500,
    "engine_temp": 92,
    "oil_pressure": 45,
    "fuel_pressure": 380,
    "battery_voltage": 14.2,
    "throttle_position": 25,
    "maf_rate": 12.5,
    "o2_voltage": 0.45,
    "vehicle_speed": 60
  },
  "fault_codes": ["P0301", "P0171", "B1234"],
  "freeze_frame": {
    "P0301": {
      "rpm": 2800,
      "engine_temp": 95,
      "vehicle_speed": 45
    }
  }
}
```

#### Audio Data
```json
{
  "scan_id": "test-001",
  "channel": "audio",
  "frequencies": [100, 500, 1000, 2000, 4000, 8000],
  "amplitudes": [45, 62, 58, 41, 35, 28],
  "peak_frequency": 500,
  "peak_amplitude": 62,
  "noise_level": 55,
  "anomalies": ["bearing_noise", "exhaust_leak"]
}
```

#### Thermal Data
```json
{
  "scan_id": "test-001",
  "channel": "thermal",
  "zones": {
    "engine": {"temp": 95, "status": "normal"},
    "exhaust": {"temp": 280, "status": "normal"},
    "brakes_front": {"temp": 120, "status": "normal"},
    "brakes_rear": {"temp": 85, "status": "normal"},
    "transmission": {"temp": 75, "status": "normal"}
  },
  "max_temp": 280,
  "min_temp": 25,
  "avg_temp": 115
}
```

#### TOF Data
```json
{
  "scan_id": "test-001",
  "channel": "tof",
  "measurements": {
    "ground_clearance": 180,
    "tire_tread_depth": {
      "front_left": 7.2,
      "front_right": 7.5,
      "rear_left": 6.8,
      "rear_right": 6.9
    },
    "brake_pad_thickness": {
      "front_left": 9.5,
      "front_right": 9.2,
      "rear_left": 8.8,
      "rear_right": 8.7
    }
  }
}
```

## Running the Tests

### Prerequisites
1. Start Docker containers: `docker-compose up -d`
2. Install Python dependencies: `pip install aiohttp paho-mqtt python-dotenv requests`

### Test Execution

#### Full E2E Test
```bash
cd tests
python3 e2e_test_scenario.py
```

#### Quick System Check
```bash
cd tests
python3 quick_test.py
```

#### MQTT Sensor Simulation
```bash
cd tests
# Single data publish
python3 mqtt_sensor_simulator.py --single --scan-id test-001

# Continuous simulation (60 seconds)
python3 mqtt_sensor_simulator.py --duration 60 --interval 5 --scan-id test-001
```

## Expected Test Results

### Success Criteria
- ✅ All API endpoints respond with correct status codes
- ✅ VIN decoder returns accurate vehicle information
- ✅ Vehicle database provides recalls and safety ratings
- ✅ MQTT sensor data is received and processed
- ✅ Diagnostic reports include health scores and recommendations
- ✅ Maintenance schedules are vehicle-specific
- ✅ Common problems are identified with severity ratings

### Key Metrics
- **Response Time**: All API calls < 2 seconds
- **Data Accuracy**: VIN decoding 100% accurate
- **Report Generation**: Complete reports with all sections
- **MQTT Reliability**: All sensor channels received
- **Health Score Calculation**: Based on fault codes and parameters

## Test Report Output

The test suite generates:
1. **Console Output**: Real-time test progress with pass/fail indicators
2. **JSON Report**: `e2e_test_report_YYYYMMDD_HHMMSS.json` with detailed results
3. **Summary Statistics**: Total tests, passed, failed, pass rate

### Report Structure
```json
{
  "timestamp": "2024-09-04T11:00:00",
  "vin": "1HGBH41JXMN109186",
  "tests": [
    {
      "timestamp": "11:00:01",
      "level": "PASS",
      "message": "VIN decoded: Honda Accord 2021"
    }
  ],
  "summary": {
    "total": 12,
    "passed": 10,
    "failed": 2
  }
}
```

## Troubleshooting

### Common Issues
1. **Backend not accessible**: Check if Docker containers are running
2. **MQTT connection failed**: Verify mosquitto broker is running
3. **VIN decoder timeout**: Check NHTSA API availability
4. **Report generation error**: Verify fault_detector module is loaded

### Debug Commands
```bash
# Check Docker containers
docker ps

# View backend logs
docker logs motospect-backend

# Test MQTT broker
mosquitto_sub -h localhost -t "motospect/v1/#" -v

# Check API health
curl http://localhost:8000/health
```

## Notes
- Test VIN `1HGBH41JXMN109186` represents a 2021 Honda Accord
- All sensor data is simulated for testing purposes
- Report generation uses the comprehensive fault detection system
- Vehicle database uses NHTSA public APIs
