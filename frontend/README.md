# MotoSpect Frontend - Service Technician Portal

## Overview
Web interface for automotive service technicians to perform vehicle diagnostics and generate reports.

## Features
- **VIN Scanner**: Quick vehicle identification via VIN
- **Real-time Diagnostics**: Live sensor data visualization
- **Multi-channel Display**: OBD, Audio, Thermal, and TOF data
- **Report Generation**: Create and download diagnostic reports
- **Fault Code Analysis**: Detailed fault code interpretation
- **Health Scoring**: Visual system health indicators

## User Interface
- Dashboard with vehicle information
- Real-time gauge displays (RPM, Temperature, Pressure)
- Fault code viewer with severity indicators
- Sensor data graphs and charts
- Report preview and download

## Technology Stack
- React 18
- Material-UI components
- WebSocket for real-time data
- Chart.js for visualizations
- PDF generation

## Running Locally
```bash
npm install
npm start
# Opens at http://localhost:3030
```

## Environment Variables
```
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_BACKEND_WS_URL=ws://localhost:8000/ws
```

## Build for Production
```bash
npm run build
```
