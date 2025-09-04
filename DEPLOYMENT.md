# MotoSpect Production Deployment Guide

## System Overview
MotoSpect is a comprehensive vehicle diagnostic system supporting cars, vans, and SUVs with engines up to 3L capacity. The system provides precise fault detection through multi-sensor data fusion and advanced analytics.

## Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- MQTT Broker (Mosquitto)

## Supported Vehicles
- **Vehicle Types**: Cars, Vans, SUVs, Crossovers, Light Trucks
- **Engine Capacity**: 1.0L to 3.0L
- **Diagnostic Protocols**: OBD-II compliant vehicles

## Architecture Components
1. **Backend Service** (Port 8000) - FastAPI-based diagnostic engine
2. **Frontend Portal** (Port 3030) - Service technician interface
3. **Customer Portal** (Port 3040) - Customer self-service
4. **Report Service** (Port 3050) - PDF report generation
5. **MQTT Broker** (Port 1883) - Sensor data communication
6. **PostgreSQL Database** - Data persistence
7. **Redis Cache** - Session and cache management

## Deployment Steps

### 1. Environment Configuration
```bash
# Copy and configure environment variables
cp .env.example .env

# Update production values:
# - Change JWT_SECRET_KEY
# - Set DATABASE_URL with production credentials
# - Configure MQTT_BROKER_HOST
# - Set TEST_MODE=false
# - Set LOG_LEVEL=INFO
```

### 2. Using Docker Compose (Recommended)
```bash
# Build all services
make build

# Start production environment
make prod

# Verify services are running
docker-compose ps

# Check logs
make logs
```

### 3. Manual Deployment

#### Backend Service
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend Applications
```bash
# Service Technician Portal
cd frontend
npm install
npm run build
npm install -g serve
serve -s build -l 3030

# Customer Portal
cd customer-portal
npm install
npm run build
serve -s build -l 3040
```

#### MQTT Broker
```bash
docker run -d \
  --name mosquitto \
  -p 1883:1883 \
  -v $(pwd)/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto
```

## Database Setup
```sql
-- Create database
CREATE DATABASE motospect_db;
CREATE USER motospect WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE motospect_db TO motospect;

-- Initialize schema (run from backend)
python3 init_database.py
```

## Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Test VIN decoder
curl http://localhost:8000/api/vin/1HGBH41JXMN109186

# MQTT broker
mosquitto_sub -t "motospect/v1/#" -C 1
```

## Monitoring

### Key Metrics to Monitor
- API response times (target < 500ms)
- MQTT message throughput
- Database connection pool usage
- Memory usage per service
- Fault detection accuracy
- Report generation time

### Logging
All services log to:
- Console (stdout/stderr)
- File: `/var/log/motospect/[service].log`
- Level: INFO (production), DEBUG (development)

## Security Checklist
- [ ] Change default passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable MQTT authentication
- [ ] Set up API rate limiting
- [ ] Configure CORS properly
- [ ] Enable database SSL
- [ ] Regular security updates

## Backup Strategy
```bash
# Database backup
pg_dump motospect_db > backup_$(date +%Y%m%d).sql

# Report archive
tar -czf reports_$(date +%Y%m%d).tar.gz /var/motospect/reports

# Configuration backup
tar -czf config_$(date +%Y%m%d).tar.gz .env mosquitto/
```

## Performance Tuning

### Backend
- Set `BACKEND_WORKERS=4` (adjust based on CPU cores)
- Configure `DATABASE_POOL_SIZE=20`
- Enable Redis caching with `CACHE_TTL=3600`

### MQTT
- Set `MQTT_QOS=1` for reliable delivery
- Configure message retention policies
- Implement topic-based ACLs

### Database
- Add indexes for VIN lookups
- Optimize query performance
- Regular VACUUM and ANALYZE

## Troubleshooting

### Common Issues
1. **Backend won't start**: Check Python dependencies and database connection
2. **MQTT connection fails**: Verify broker is running and ports are open
3. **Report generation slow**: Check memory allocation and PDF library
4. **VIN decoder errors**: Verify NHTSA API connectivity

### Debug Commands
```bash
# Check service logs
docker-compose logs -f [service-name]

# Test database connection
python3 -c "from backend.database import test_connection; test_connection()"

# Verify MQTT publishing
python3 tests/mqtt_sensor_simulator.py --single

# Run system tests
make test-quick
```

## Scaling Considerations

### Horizontal Scaling
- Backend: Deploy multiple instances behind load balancer
- MQTT: Use MQTT broker clustering
- Database: Implement read replicas

### Vertical Scaling
- Minimum: 4 CPU, 8GB RAM
- Recommended: 8 CPU, 16GB RAM
- Database: SSD storage recommended

## Support Matrix

### Diagnostic Capabilities by Engine Size
| Engine Size | RPM Range | Pressure (PSI) | Temp (°C) |
|------------|-----------|----------------|-----------|
| 1.0L-1.4L  | 600-6500  | 20-45         | 80-105    |
| 1.5L-1.9L  | 650-6500  | 22-48         | 82-108    |
| 2.0L-2.4L  | 700-6000  | 25-50         | 85-110    |
| 2.5L-3.0L  | 750-5500  | 30-55         | 88-112    |

### Fault Code Coverage
- Engine: P0001-P0999
- Transmission: P0700-P0899
- Emissions: P0400-P0499
- Speed/Idle: P0500-P0599
- Computer/Auxiliary: P0600-P0699

## Maintenance

### Daily
- Monitor service health
- Check error logs
- Verify MQTT connectivity

### Weekly
- Database backup
- Clear old logs
- Update fault code database

### Monthly
- Security updates
- Performance review
- Storage cleanup

## Contact & Support
- Technical Issues: Create issue in GitHub repository
- Security Concerns: Email security@motospect.com
- Documentation: See /docs folder

## Version History
- v1.0.0 - Initial release with 3L engine support
- v1.1.0 - Added predictive analysis
- v1.2.0 - Multi-sensor fusion capability
