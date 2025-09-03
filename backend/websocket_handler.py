import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from data_generator import generate_scan_data

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
            data = generate_scan_data()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)  # Symulacja ciągłego skanowania
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
