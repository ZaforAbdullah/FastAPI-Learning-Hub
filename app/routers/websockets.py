import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """
    Echo server — sends back whatever the client sends.

        wscat -c ws://localhost:8000/ws/echo
        > hello
        < {"echo": "hello", "timestamp": "..."}
    """
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({
                "echo": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        pass


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(room, set()).add(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        if room in self.rooms:
            self.rooms[room].discard(ws)
            if not self.rooms[room]:
                del self.rooms[room]

    async def broadcast(self, room: str, message: dict) -> None:
        dead = set()
        for ws in self.rooms.get(room, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.rooms.get(room, set()).difference_update(dead)

    def count(self, room: str) -> int:
        return len(self.rooms.get(room, set()))


manager = ConnectionManager()


@router.websocket("/ws/chat/{room}/{username}")
async def websocket_chat(room: str, username: str, websocket: WebSocket):
    """
    Broadcast chat room — all clients in a room receive every message.

        wscat -c ws://localhost:8000/ws/chat/general/alice
        wscat -c ws://localhost:8000/ws/chat/general/bob
    """
    await manager.connect(room, websocket)
    await manager.broadcast(room, {
        "type": "system",
        "message": f"{username} joined",
        "online": manager.count(room),
    })
    try:
        while True:
            text = await websocket.receive_text()
            try:
                content = json.loads(text).get("message", text)
            except json.JSONDecodeError:
                content = text
            await manager.broadcast(room, {
                "type": "message",
                "username": username,
                "message": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
        await manager.broadcast(room, {
            "type": "system",
            "message": f"{username} left",
            "online": manager.count(room),
        })


@router.websocket("/ws/live-feed")
async def live_feed(websocket: WebSocket):
    """
    Server pushes a price tick every second for 20 ticks.

        wscat -c ws://localhost:8000/ws/live-feed
    """
    await websocket.accept()
    try:
        for tick in range(20):
            await websocket.send_json({
                "tick": tick,
                "price": round(100 + random.uniform(-5, 5), 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            await asyncio.sleep(1)
        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
    except WebSocketDisconnect:
        pass
