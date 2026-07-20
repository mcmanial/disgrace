import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import async_session
from app.models import Message, Room, User

router = APIRouter()


class RoomConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[int, dict[WebSocket, User]] = {}

    async def connect(self, room_id: int, websocket: WebSocket, user: User) -> None:
        await websocket.accept()
        self.rooms.setdefault(room_id, {})

        await websocket.send_json(
            {"event": "presence_state", "payload": self._presence(room_id)}
        )
        self.rooms[room_id][websocket] = user
        await self._broadcast(
            room_id,
            {"event": "presence_diff", "payload": {"joins": {str(user.id): self._user_info(user)}, "leaves": {}}},
            skip=websocket,
        )

    async def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        user = self.rooms.get(room_id, {}).pop(websocket, None)
        if user is None:
            return
        await self._broadcast(
            room_id,
            {"event": "presence_diff", "payload": {"joins": {}, "leaves": {str(user.id): self._user_info(user)}}},
        )

    async def broadcast_message(self, room_id: int, message: Message, sender: User) -> None:
        await self._broadcast(
            room_id,
            {
                "event": "new_message",
                "payload": {
                    "id": message.id,
                    "room_id": message.room_id,
                    "user_id": message.user_id,
                    "user_name": sender.name,
                    "user_avatar": sender.avatar_url,
                    "body": message.body,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    def _user_info(self, user: User) -> dict:
        return {"name": user.name, "avatar_url": user.avatar_url}

    def _presence(self, room_id: int) -> dict:
        return {str(user.id): self._user_info(user) for user in self.rooms.get(room_id, {}).values()}

    async def _broadcast(self, room_id: int, message: dict, skip: WebSocket | None = None) -> None:
        for ws in list(self.rooms.get(room_id, {})):
            if ws is not skip:
                await ws.send_json(message)


manager = RoomConnectionManager()


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: int):
    user_id = websocket.session.get("user_id")
    if user_id is None:
        await websocket.accept()
        await websocket.close(code=4401)
        return

    async with async_session() as db:
        user = await db.get(User, user_id)
        room = await db.get(Room, room_id)
        if user is None or room is None:
            await websocket.accept()
            await websocket.close(code=4404)
            return

    await manager.connect(room_id, websocket, user)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            body = data.get("body", "").strip()
            if not body:
                continue

            async with async_session() as db:
                message = Message(room_id=room_id, user_id=user.id, body=body)
                db.add(message)
                await db.commit()
                await db.refresh(message)

            await manager.broadcast_message(room_id, message, user)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room_id, websocket)
