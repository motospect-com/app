import asyncio
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from data_generator import (
    generate_tof_scan_data,
    generate_thermal_scan_data,
    generate_uv_scan_data,
    generate_paint_thickness_data,
)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket do przesyłania danych skanowania.

    Args:
        websocket (WebSocket): Obiekt WebSocket.
    """
    await websocket.accept()
    try:
        while True:
            # Basic multiplexing: emit frames for all available channels
            frames = [
                generate_tof_scan_data(),
                generate_thermal_scan_data(),
                generate_uv_scan_data(),
                generate_paint_thickness_data(),
            ]
            now = time.time()
            for data in frames:
                data["channel"] = data.get("scan_type")
                data["ts"] = now
                await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)  # Symulacja ciągłego skanowania
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
