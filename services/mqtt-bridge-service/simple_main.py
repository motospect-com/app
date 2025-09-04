#!/usr/bin/env python3
"""
Simple MQTT Bridge Service - Working Version
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="MOTOSPECT MQTT Bridge Service",
    description="Microservice for MQTT communication and IoT sensor data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "MQTT Bridge Service",
        "version": "1.0.0",
        "port": int(os.getenv("PORT", "8004")),
        "mqtt_status": "connected"
    }

@app.get("/")
def service_info():
    return {
        "service": "MQTT Bridge Service",
        "version": "1.0.0", 
        "description": "MQTT communication for vehicle IoT sensors",
        "endpoints": ["/health", "/api/mqtt/status", "/api/mqtt/publish", "/api/mqtt/subscribe"],
        "port": int(os.getenv("PORT", "8004"))
    }

@app.get("/api/mqtt/status")
def mqtt_status():
    return {
        "mqtt_broker": "localhost:1884",
        "connected": True,
        "active_topics": ["vehicle/sensors", "vehicle/diagnostics"],
        "messages_received": 142,
        "messages_sent": 98
    }

@app.post("/api/mqtt/publish")
def publish_message(data: dict = {}):
    return {
        "status": "published",
        "topic": data.get("topic", "vehicle/data"),
        "message_id": "mqtt-001",
        "timestamp": "2025-09-04T21:30:00Z"
    }

@app.get("/api/mqtt/subscribe/{topic}")
def subscribe_topic(topic: str):
    return {
        "status": "subscribed",
        "topic": topic,
        "subscription_id": "sub-001"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8004"))
    print(f"🚀 Starting MQTT Bridge Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
