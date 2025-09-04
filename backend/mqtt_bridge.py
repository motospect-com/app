import json
import os
import threading
from typing import Dict, Optional

import paho.mqtt.client as mqtt
from fastapi import APIRouter, HTTPException


class MqttBridge:
    def __init__(self) -> None:
        self.host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.base_topic: str = os.getenv("MQTT_BASE_TOPIC", "motospect/v1")
        self._client: Optional[mqtt.Client] = None
        self._lock = threading.Lock()
        self._latest: Dict[str, Dict] = {}
        self._connected = False

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            client.subscribe(f"{self.base_topic}/+")
        else:
            print(f"[mqtt_bridge] connect failed rc={rc}")

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            channel = payload.get("channel") or payload.get("scan_type") or "unknown"
            with self._lock:
                self._latest[channel] = payload
        except Exception as e:
            print(f"[mqtt_bridge] bad payload on {msg.topic}: {e}")

    def start(self) -> None:
        if self._client is not None:
            return
        self._client = mqtt.Client(client_id="backend-bridge")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect(self.host, self.port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        finally:
            self._client = None
            self._connected = False

    def latest(self, channel: Optional[str] = None) -> Dict:
        with self._lock:
            if channel is None:
                return dict(self._latest)
            if channel not in self._latest:
                raise KeyError(channel)
            return self._latest[channel]

    def publish(self, topic_suffix: str, payload: Dict) -> None:
        if self._client is None:
            raise RuntimeError("MQTT client not started")
        topic = f"{self.base_topic}/{topic_suffix.lstrip('/')}"
        self._client.publish(topic, json.dumps(payload), qos=0, retain=False)


def is_enabled() -> bool:
    return os.getenv("ENABLE_MQTT_BRIDGE", "true").lower() == "true"


bridge = MqttBridge()

router = APIRouter()


@router.get("/api/latest")
async def api_latest_all():
    try:
        return {"data": bridge.latest()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/latest/{channel}")
async def api_latest_channel(channel: str):
    try:
        return {"channel": channel, "data": bridge.latest(channel)}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no data for channel '{channel}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cmd/{topic_suffix}")
async def api_publish_cmd(topic_suffix: str, body: Dict):
    if not is_enabled():
        raise HTTPException(status_code=503, detail="MQTT bridge disabled")
    try:
        bridge.publish(topic_suffix, body)
        return {"status": "published"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
