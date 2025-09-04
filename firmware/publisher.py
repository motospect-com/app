import json
import os
import random
import time
from typing import Dict, List

import numpy as np
import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "motospect/v1")
PUBLISH_HZ = float(os.getenv("PUBLISH_HZ", "1"))

# --- Mock generators (standalone to avoid coupling with backend package) ---

def gen_points(n: int = 1000) -> List[List[float]]:
    return (np.random.rand(n, 3) * 100).tolist()


def gen_tof() -> Dict:
    pts = gen_points()
    colors = np.random.randint(0, 255, size=(len(pts), 3)).tolist()
    return {"scan_type": "tof", "points": pts, "colors": colors}


def gen_thermal() -> Dict:
    pts = gen_points()
    temps = np.random.uniform(20.0, 100.0, size=len(pts)).tolist()
    return {"scan_type": "thermal", "points": pts, "temperatures": temps}


def gen_uv() -> Dict:
    pts = gen_points()
    intensity = np.random.uniform(0.0, 1.0, size=len(pts)).tolist()
    return {"scan_type": "uv", "points": pts, "intensity": intensity}


def gen_paint() -> Dict:
    pts = gen_points()
    thickness = np.random.uniform(80.0, 200.0, size=len(pts)).tolist()
    return {"scan_type": "paint_thickness", "points": pts, "thickness": thickness}


def gen_audio() -> Dict:
    level = float(np.random.uniform(0.0, 1.0))
    spectrum = np.random.uniform(0.0, 1.0, size=64).tolist()
    return {"scan_type": "audio", "level": level, "spectrum": spectrum}


def main() -> None:
    client = mqtt.Client(client_id=f"firmware-pub-{random.randint(1000,9999)}")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_start()

    interval = 1.0 / max(0.1, PUBLISH_HZ)
    print(f"[firmware] publishing to mqtt://{BROKER_HOST}:{BROKER_PORT}, base topic '{BASE_TOPIC}', every {interval:.2f}s")

    try:
        while True:
            ts = time.time()
            frames = [
                ("tof", gen_tof()),
                ("thermal", gen_thermal()),
                ("uv", gen_uv()),
                ("paint_thickness", gen_paint()),
                ("audio", gen_audio()),
            ]
            for channel, payload in frames:
                payload["channel"] = channel
                payload["ts"] = ts
                topic = f"{BASE_TOPIC}/{channel}"
                client.publish(topic, json.dumps(payload), qos=0, retain=False)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
