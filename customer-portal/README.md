# MotoSpect Customer Portal

## Overview
Self-service portal for vehicle owners to view diagnostic reports and maintenance information.

## Features
- **Report Access**: View and download diagnostic reports
- **Scan Status**: Real-time scan progress tracking
- **Gate Simulation**: Virtual diagnostic gate interface
- **Maintenance Schedule**: Personalized maintenance recommendations
- **Common Problems**: Known issues for your vehicle
- **Report History**: Access previous diagnostic reports

## User Journey
1. Enter through virtual diagnostic gate
2. Vehicle automatically identified via sensors
3. View real-time scan progress
4. Access comprehensive diagnostic report
5. Download PDF report for records
6. View maintenance recommendations

## Technology Stack
- React 18
- Material-UI
- Real-time WebSocket updates
- PDF viewer integration

## Running Locally
```bash
npm install
npm start
# Opens at http://localhost:3040
```

## Environment Variables
```
REACT_APP_CUSTOMER_API_URL=http://localhost:8000
```

## Build for Production
```bash
npm run build
```
