# MotoSpect Report Service

## Overview
Microservice for generating and managing diagnostic reports with PDF export capabilities.

## Features
- PDF report generation
- Report template management
- Historical report storage
- Email delivery (optional)
- Report analytics

## API Endpoints
- `GET /api/report/{id}` - Get report by ID
- `GET /api/report/{id}/pdf` - Download PDF
- `POST /api/report/generate` - Generate new report
- `GET /api/report/template` - Get report templates

## Report Contents
- Vehicle information
- Fault codes with descriptions
- System health scores
- Maintenance recommendations
- Sensor data visualizations
- Cost estimates

## Running
```bash
npm install
npm start
# Service runs on port 3050
```

## Environment Variables
```
REACT_APP_REPORT_API_URL=http://localhost:8000
REPORT_SERVICE_PORT=3050
```
