import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, host_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(host_id, []).append(websocket)

    def disconnect(self, host_id: str, websocket: WebSocket) -> None:
        conns = self.active.get(host_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, host_id: str, message: dict[str, Any]) -> None:
        payload = json.dumps(message)
        for ws in list(self.active.get(host_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                self.disconnect(host_id, ws)


ws_manager = ConnectionManager()
