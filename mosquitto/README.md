# MotoSpect MQTT Broker

## Overview
MQTT message broker for real-time sensor data communication between diagnostic hardware and backend services.

## Configuration
The `mosquitto.conf` file configures:
- Port: 1883 (default MQTT port)
- Anonymous access: allowed for local development
- Logging: enabled for debugging

## MQTT Topics Structure
```
motospect/v1/
├── obd         # OBD-II diagnostic data
├── audio       # Audio spectrum analysis
├── thermal     # Thermal camera data
├── tof         # Time-of-flight sensor data
└── status      # System status updates
```

## Message Format
All messages use JSON format with standard structure:
```json
{
  "scan_id": "unique-scan-id",
  "channel": "channel-name",
  "timestamp": "ISO-8601",
  "data": { /* channel-specific data */ }
}
```

## Running
```bash
# Using Docker
docker run -p 1883:1883 -v $(pwd)/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto

# Test connection
mosquitto_sub -t "motospect/v1/#" -v
```

## Security (Production)
For production deployment:
1. Enable authentication
2. Use TLS/SSL encryption
3. Implement ACL for topic access
4. Disable anonymous access
