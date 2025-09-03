import json
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)


def test_websocket_connection():
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_text()
        scan_data = json.loads(data)

        assert "scan_type" in scan_data
        assert "points" in scan_data

        scan_type = scan_data["scan_type"]
        if scan_type == "tof":
            assert "colors" in scan_data
        elif scan_type == "thermal":
            assert "temperatures" in scan_data
        elif scan_type == "uv":
            assert "intensity" in scan_data
        elif scan_type == "paint_thickness":
            assert "thickness" in scan_data
