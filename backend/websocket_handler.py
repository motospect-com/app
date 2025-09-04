import asyncio
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from data_generator import (
    generate_tof_scan_data,
    generate_thermal_scan_data,
    generate_uv_scan_data,
    generate_paint_thickness_data,
    generate_audio_data,
)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time scan data streaming.

    Args:
        websocket (WebSocket): WebSocket connection instance.
    """
    # Set CORS headers for WebSocket
    origin = websocket.headers.get('origin')
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8084",
    ]
    
    if origin and origin not in allowed_origins:
        print(f"WebSocket connection rejected: Origin {origin} not allowed")
        await websocket.close(code=1008)  # Policy Violation
        return

    await websocket.accept()
    print("WebSocket connection established")
    
    try:
        while True:
            try:
                # Basic multiplexing: emit frames for all available channels
                frames = [
                    generate_tof_scan_data(),
                    generate_thermal_scan_data(),
                    generate_uv_scan_data(),
                    generate_paint_thickness_data(),
                    generate_audio_data(),
                ]
                now = time.time()
                for data in frames:
                    data["channel"] = data.get("scan_type")
                    data["ts"] = now
                    await websocket.send_text(json.dumps(data))
                await asyncio.sleep(1)  # Simulate continuous scanning
                
                # Send a ping to keep the connection alive
                await websocket.send_json({"type": "ping", "timestamp": now})
                
            except asyncio.CancelledError:
                print("WebSocket connection cancelled")
                break
                
    except WebSocketDisconnect as e:
        print(f"Client disconnected: {e.code if hasattr(e, 'code') else 'No code'}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011)  # Internal Error
        except:
            pass
    finally:
        print("WebSocket connection closed")
