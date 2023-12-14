from typing import Any, Awaitable, Callable
import uuid
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from demoapp.models import json_default


class WebSocketManager:
    def __init__(self, on_connection: Callable[[WebSocket], Awaitable[None]] = None):
        self.connections: dict[str, WebSocket] = {}
        self.on_connection = on_connection

    async def new_connection(self, websocket: WebSocket):
        await websocket.accept()

        id = str(uuid.uuid4())
        self.connections[id] = websocket
        logging.info("WebSocket: new link connection: %s", id)

        if self.on_connection:
            await self.on_connection(websocket)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logging.info("WebSocket: link disconnect: %s", id)
            del self.connections[id]

    async def send_message(self, dto: BaseModel):
        await self.send_messages([dto])

    async def send_messages(self, data: list[BaseModel]):
        for id, con in self.connections.items():
            logging.info("WebSocket: send messages to connection=%s", id)
            await self.send_json(con, [x.model_dump() for x in data])

    @staticmethod
    async def send_json(connection: WebSocket, data: Any):
        await connection.send_text(json.dumps(data, default=json_default))