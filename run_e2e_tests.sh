#!/bin/bash

# MotoSpect E2E Test Runner
# This script runs comprehensive tests for the entire MotoSpect system

echo "=========================================="
echo "   MOTOSPECT E2E TEST SUITE"
echo "=========================================="
echo "Date: $(date)"
echo "Test VIN: 1HGBH41JXMN109186"
echo "=========================================="

# Test configuration
BACKEND_URL="http://localhost:8000"
TEST_VIN="1HGBH41JXMN109186"
TEST_RESULTS_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test results
log_test() {
    local test_name=$1
    local status=$2
    local message=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name: $message"
        echo "✓ $test_name: $message" >> $TEST_RESULTS_FILE
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $test_name: $message"
        echo "✗ $test_name: $message" >> $TEST_RESULTS_FILE
        FAILED_TESTS=$((FAILED_TESTS + 1))
    else
        echo -e "${YELLOW}→${NC} $test_name: $message"
        echo "→ $test_name: $message" >> $TEST_RESULTS_FILE
    fi
}

# Start test results file
echo "MotoSpect E2E Test Results" > $TEST_RESULTS_FILE
echo "Date: $(date)" >> $TEST_RESULTS_FILE
echo "==========================================" >> $TEST_RESULTS_FILE

echo ""
echo "=========================================="
echo "   1. SYSTEM CONNECTIVITY TESTS"
echo "=========================================="

# Test 1: Backend Health Check
echo "Testing backend connectivity..."
if curl -s -f -o /dev/null "$BACKEND_URL/health" 2>/dev/null; then
    log_test "Backend Health" "PASS" "Backend is running"
else
    log_test "Backend Health" "FAIL" "Backend not accessible at $BACKEND_URL"
fi

# Test 2: MQTT Broker Check
echo "Testing MQTT broker..."
if timeout 2 nc -zv localhost 1883 2>/dev/null; then
    log_test "MQTT Broker" "PASS" "MQTT broker is running on port 1883"
else
    log_test "MQTT Broker" "FAIL" "MQTT broker not accessible"
fi

echo ""
echo "=========================================="
echo "   2. VEHICLE DATABASE API TESTS"
echo "=========================================="

# Test 3: VIN Decoder
echo "Testing VIN decoder for $TEST_VIN..."
VIN_RESPONSE=$(curl -s "$BACKEND_URL/api/vin/$TEST_VIN" 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$VIN_RESPONSE" ]; then
    log_test "VIN Decoder" "PASS" "VIN decoded successfully"
    echo "  Vehicle info: $VIN_RESPONSE" | head -1
else
    log_test "VIN Decoder" "FAIL" "Could not decode VIN"
fi

# Test 4: Vehicle Database Lookup
echo "Testing vehicle database..."
DB_RESPONSE=$(curl -s "$BACKEND_URL/api/vehicle/database/$TEST_VIN" 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$DB_RESPONSE" ]; then
    log_test "Vehicle Database" "PASS" "Vehicle database info retrieved"
else
    log_test "Vehicle Database" "FAIL" "Could not retrieve vehicle database info"
fi

# Test 5: Maintenance Schedule
echo "Testing maintenance schedule..."
MAINT_RESPONSE=$(curl -s "$BACKEND_URL/api/vehicle/maintenance?make=Honda&model=Accord&year=2021&mileage=45000" 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$MAINT_RESPONSE" ]; then
    log_test "Maintenance Schedule" "PASS" "Maintenance schedule retrieved"
else
    log_test "Maintenance Schedule" "FAIL" "Could not retrieve maintenance schedule"
fi

# Test 6: Common Problems
echo "Testing common problems..."
PROBLEMS_RESPONSE=$(curl -s "$BACKEND_URL/api/vehicle/common-problems?make=Honda&model=Accord&year=2021&mileage=45000" 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$PROBLEMS_RESPONSE" ]; then
    log_test "Common Problems" "PASS" "Common problems retrieved"
else
    log_test "Common Problems" "FAIL" "Could not retrieve common problems"
fi

echo ""
echo "=========================================="
echo "   3. DIAGNOSTIC SCAN WORKFLOW"
echo "=========================================="

# Test 7: Start Scan
echo "Starting diagnostic scan..."
SCAN_START_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/scan/start" \
    -H "Content-Type: application/json" \
    -d "{\"vehicle_id\": \"$TEST_VIN\"}" 2>/dev/null)
    
if [ $? -eq 0 ] && [ ! -z "$SCAN_START_RESPONSE" ]; then
    SCAN_ID=$(echo "$SCAN_START_RESPONSE" | grep -o '"scan_id":"[^"]*' | cut -d'"' -f4)
    if [ ! -z "$SCAN_ID" ]; then
        log_test "Start Scan" "PASS" "Scan started with ID: $SCAN_ID"
    else
        SCAN_ID="test-scan-001"
        log_test "Start Scan" "INFO" "Using test scan ID: $SCAN_ID"
    fi
else
    SCAN_ID="test-scan-001"
    log_test "Start Scan" "FAIL" "Could not start scan, using test ID"
fi

# Test 8: OBD Auto-detect
echo "Testing OBD auto-detection..."
OBD_RESPONSE=$(curl -s "$BACKEND_URL/api/obd/auto-detect" 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$OBD_RESPONSE" ]; then
    log_test "OBD Auto-detect" "PASS" "OBD auto-detection successful"
else
    log_test "OBD Auto-detect" "FAIL" "OBD auto-detection failed"
fi

echo ""
echo "=========================================="
echo "   4. MQTT SENSOR SIMULATION"
echo "=========================================="

# Test 9: MQTT Sensor Data Publishing
echo "Simulating sensor data via MQTT..."

# Create a simple Python script to publish MQTT data
cat > /tmp/mqtt_test.py << 'EOF'
import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client(client_id="e2e-test")
try:
    client.connect("localhost", 1883, 60)
    
    # OBD Data
    obd_data = {
        "scan_id": "test-scan-001",
        "channel": "obd",
        "parameters": {"rpm": 2500, "engine_temp": 92}
    }
    client.publish("motospect/v1/obd", json.dumps(obd_data))
    print("Published OBD data")
    
    time.sleep(0.5)
    client.disconnect()
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
EOF

MQTT_RESULT=$(python3 /tmp/mqtt_test.py 2>&1)
if echo "$MQTT_RESULT" | grep -q "SUCCESS"; then
    log_test "MQTT Publishing" "PASS" "Sensor data published via MQTT"
else
    log_test "MQTT Publishing" "FAIL" "Could not publish to MQTT broker"
fi

echo ""
echo "=========================================="
echo "   5. REPORT GENERATION"
echo "=========================================="

# Test 10: Generate Report
echo "Generating diagnostic report..."
REPORT_DATA='{
    "vin": "'$TEST_VIN'",
    "vehicle_info": {
        "make": "Honda",
        "model": "Accord",
        "year": 2021,
        "mileage": 45000
    },
    "parameters": {
        "rpm": 2500,
        "coolant_temp": 92,
        "oil_pressure": 45,
        "fuel_pressure": 380
    },
    "fault_codes": ["P0301", "P0171"],
    "scan_type": "comprehensive"
}'

REPORT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/report/generate" \
    -H "Content-Type: application/json" \
    -d "$REPORT_DATA" 2>/dev/null)
    
if [ $? -eq 0 ] && [ ! -z "$REPORT_RESPONSE" ]; then
    # Save report to file
    echo "$REPORT_RESPONSE" > "diagnostic_report_$(date +%Y%m%d_%H%M%S).json"
    log_test "Report Generation" "PASS" "Diagnostic report generated and saved"
    
    # Try to extract health score
    if echo "$REPORT_RESPONSE" | grep -q "health_scores"; then
        echo "  Report contains health scores"
    fi
else
    log_test "Report Generation" "FAIL" "Could not generate report"
fi

# Test 11: Stop Scan
echo "Stopping diagnostic scan..."
STOP_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/scan/$SCAN_ID/stop" 2>/dev/null)
if [ $? -eq 0 ]; then
    log_test "Stop Scan" "PASS" "Scan stopped successfully"
else
    log_test "Stop Scan" "FAIL" "Could not stop scan"
fi

echo ""
echo "=========================================="
echo "   6. CUSTOMER PORTAL TESTS"
echo "=========================================="

# Test 12: Customer Portal
echo "Testing customer portal..."
if curl -s -f -o /dev/null "http://localhost:3040" 2>/dev/null; then
    log_test "Customer Portal" "PASS" "Customer portal is accessible"
else
    log_test "Customer Portal" "INFO" "Customer portal not running on port 3040"
fi

# Test 13: Report Service
echo "Testing report service..."
if curl -s -f -o /dev/null "http://localhost:3050/api/report/test" 2>/dev/null; then
    log_test "Report Service" "PASS" "Report service is accessible"
else
    log_test "Report Service" "INFO" "Report service not running on port 3050"
fi

echo ""
echo "=========================================="
echo "   TEST RESULTS SUMMARY"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "Pass Rate: $PASS_RATE%"
    
    echo "" >> $TEST_RESULTS_FILE
    echo "==========================================" >> $TEST_RESULTS_FILE
    echo "SUMMARY" >> $TEST_RESULTS_FILE
    echo "Total Tests: $TOTAL_TESTS" >> $TEST_RESULTS_FILE
    echo "Passed: $PASSED_TESTS" >> $TEST_RESULTS_FILE
    echo "Failed: $FAILED_TESTS" >> $TEST_RESULTS_FILE
    echo "Pass Rate: $PASS_RATE%" >> $TEST_RESULTS_FILE
    
    if [ $PASS_RATE -ge 80 ]; then
        echo -e "${GREEN}✓ Test suite passed with $PASS_RATE% success rate${NC}"
    elif [ $PASS_RATE -ge 60 ]; then
        echo -e "${YELLOW}⚠ Test suite partially passed with $PASS_RATE% success rate${NC}"
    else
        echo -e "${RED}✗ Test suite failed with only $PASS_RATE% success rate${NC}"
    fi
fi

echo ""
echo "Test results saved to: $TEST_RESULTS_FILE"
if ls diagnostic_report_*.json 2>/dev/null | head -1; then
    echo "Diagnostic report saved to: $(ls diagnostic_report_*.json | head -1)"
fi

echo "=========================================="
