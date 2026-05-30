from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.ws_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/v1/live")
async def live_ws(websocket: WebSocket, host_id: str) -> None:
    await ws_manager.connect(host_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(host_id, websocket)
