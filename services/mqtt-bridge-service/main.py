#!/usr/bin/env python3
"""
MQTT Bridge Microservice
Independent service for MQTT communication and IoT data handling
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import sys
import uvicorn
import asyncio
import json
from pathlib import Path
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import queue

# Add backend and infrastructure paths for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
infrastructure_path = Path(__file__).parent.parent.parent / "infrastructure"
sys.path.append(str(backend_path))
sys.path.append(str(infrastructure_path))

from config import config

try:
    from mqtt_service_bus import MQTTServiceBus
except ImportError:
    # Fallback if mqtt_service_bus doesn't exist
    MQTTServiceBus = None

app = FastAPI(
    title="MOTOSPECT MQTT Bridge Service",
    description="Microservice for MQTT communication and IoT sensor data processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MQTT client and data storage
mqtt_client = None
sensor_data_queue = queue.Queue(maxsize=1000)
connected_websockets = []
mqtt_connected = False

class SensorData(BaseModel):
    vehicle_id: str
    timestamp: str
    sensor_type: str
    value: float
    unit: str

class MQTTMessage(BaseModel):
    topic: str
    payload: Dict
    qos: int = 1

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    port: int
    mqtt_connected: bool

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("✅ Connected to MQTT broker")
        # Subscribe to MOTOSPECT topics
        client.subscribe("motospect/+/+/sensors/+")
        client.subscribe("motospect/+/+/diagnostics/+")
        client.subscribe("motospect/vehicles/+/data")
    else:
        mqtt_connected = False
        print(f"❌ Failed to connect to MQTT broker: {rc}")

def on_mqtt_message(client, userdata, msg):
    """MQTT message callback"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        # Add to sensor data queue
        sensor_data = {
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            "qos": msg.qos
        }
        
        if not sensor_data_queue.full():
            sensor_data_queue.put(sensor_data)
        
        # Broadcast to WebSocket clients
        asyncio.create_task(broadcast_to_websockets(sensor_data))
        
        print(f"📨 Received MQTT message on {topic}")
        
    except Exception as e:
        print(f"❌ Error processing MQTT message: {e}")

def on_mqtt_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    global mqtt_connected
    mqtt_connected = False
    print("🔌 Disconnected from MQTT broker")

def init_mqtt():
    """Initialize MQTT client"""
    global mqtt_client
    
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_user = os.getenv("MQTT_USER", "motospect")
    mqtt_password = os.getenv("MQTT_PASSWORD", "motospect123")
    
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(mqtt_user, mqtt_password)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.on_disconnect = on_mqtt_disconnect
    
    try:
        mqtt_client.connect(mqtt_host, mqtt_port, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"❌ Failed to connect to MQTT: {e}")

async def broadcast_to_websockets(data):
    """Broadcast data to all connected WebSocket clients"""
    if connected_websockets:
        message = json.dumps(data)
        disconnected = []
        
        for websocket in connected_websockets:
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            connected_websockets.remove(ws)

@app.on_event("startup")
async def startup_event():
    """Initialize MQTT connection on startup"""
    init_mqtt()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="mqtt-bridge-service",
        version="1.0.0",
        port=int(os.getenv("PORT", "8004")),
        mqtt_connected=mqtt_connected
    )

@app.post("/api/mqtt/publish")
async def publish_message(message: MQTTMessage):
    """Publish message to MQTT broker"""
    try:
        if not mqtt_client or not mqtt_connected:
            raise HTTPException(status_code=503, detail="MQTT broker not connected")
        
        payload = json.dumps(message.payload)
        mqtt_client.publish(message.topic, payload, message.qos)
        
        return {
            "status": "published",
            "topic": message.topic,
            "payload_size": len(payload)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing message: {str(e)}")

@app.get("/api/mqtt/sensor-data")
async def get_sensor_data(limit: int = 10):
    """Get recent sensor data"""
    data = []
    count = 0
    
    # Get data from queue (non-blocking)
    while count < limit and not sensor_data_queue.empty():
        try:
            data.append(sensor_data_queue.get_nowait())
            count += 1
        except queue.Empty:
            break
    
    return {
        "sensor_data": data,
        "count": len(data),
        "queue_size": sensor_data_queue.qsize()
    }

@app.get("/api/mqtt/topics")
async def get_topics():
    """Get available MQTT topics"""
    return {
        "available_topics": [
            "motospect/vehicles/{vehicle_id}/data",
            "motospect/sensors/{sensor_type}/{vehicle_id}",
            "motospect/diagnostics/{vehicle_id}/results",
            "motospect/alerts/{vehicle_id}/critical"
        ],
        "description": "MOTOSPECT MQTT topic structure"
    }

@app.websocket("/ws/mqtt")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MQTT data"""
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

@app.post("/api/mqtt/vehicle-data/{vehicle_id}")
async def receive_vehicle_data(vehicle_id: str, sensor_data: List[SensorData]):
    """Receive and forward vehicle sensor data"""
    try:
        if not mqtt_client or not mqtt_connected:
            raise HTTPException(status_code=503, detail="MQTT broker not connected")
        
        published_count = 0
        for data in sensor_data:
            topic = f"motospect/vehicles/{vehicle_id}/sensors/{data.sensor_type}"
            payload = {
                "vehicle_id": vehicle_id,
                "sensor_type": data.sensor_type,
                "value": data.value,
                "unit": data.unit,
                "timestamp": data.timestamp
            }
            
            mqtt_client.publish(topic, json.dumps(payload), 1)
            published_count += 1
        
        return {
            "vehicle_id": vehicle_id,
            "published_messages": published_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error receiving vehicle data: {str(e)}")

@app.get("/api/mqtt/status")
async def get_mqtt_status():
    """Get MQTT service status"""
    return {
        "mqtt_connected": mqtt_connected,
        "queue_size": sensor_data_queue.qsize(),
        "websocket_connections": len(connected_websockets),
        "broker_host": os.getenv("MQTT_HOST", "localhost"),
        "broker_port": int(os.getenv("MQTT_PORT", "1883"))
    }

@app.get("/api/mqtt/info")
async def service_info():
    """Get service information"""
    return {
        "service": "MQTT Bridge Service",
        "version": "1.0.0",
        "description": "Independent microservice for MQTT communication and IoT data",
        "endpoints": [
            "/health",
            "/api/mqtt/publish",
            "/api/mqtt/sensor-data",
            "/api/mqtt/topics",
            "/ws/mqtt",
            "/api/mqtt/vehicle-data/{vehicle_id}",
            "/api/mqtt/status"
        ],
        "port": int(os.getenv("PORT", config.MQTT_BRIDGE_SERVICE_PORT)),
        "mqtt_features": ["real-time data", "WebSocket streaming", "vehicle sensors"]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", config.MQTT_BRIDGE_SERVICE_PORT))
    print(f"🚀 Starting MQTT Bridge Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
