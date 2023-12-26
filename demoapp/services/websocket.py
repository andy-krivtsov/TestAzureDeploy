from typing import Any, Awaitable, Callable, Optional, Sequence
import uuid
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from fastapi_msal import UserInfo
from pydantic import BaseModel, Field
from demoapp.models import json_default
from opentelemetry.trace import get_tracer, SpanKind, get_current_span, Link
from opentelemetry.context import Context
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry import baggage
from opentelemetry import context

tracer = get_tracer(__name__)

class ConnectionInfo:
    def __init__(self, websocket: WebSocket, user_info: UserInfo = None):
        self.websocket = websocket
        self.user_info = user_info

class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, ConnectionInfo] = {}

    async def start_receiving(self, id: str, on_received: Callable[[Any], Awaitable[None]] = None):
        con = self.connections[id]
        try:
            while True:
                data_text = await con.websocket.receive_text()
                if on_received:
                    ctx_token = None
                    try:
                        username = con.user_info.preferred_username if con.user_info else ""
                        with tracer.start_as_current_span(
                                name="websocket.receive_frontend_message",
                                context=Context(),
                                kind=SpanKind.SERVER,
                                record_exception=True,
                                attributes={
                                    SpanAttributes.ENDUSER_ID: username,
                                    "demoapp.websocket_id": id
                                }):
                            ctx = baggage.set_baggage(SpanAttributes.ENDUSER_ID, username)
                            ctx_token = context.attach(ctx)

                            await on_received(json.loads(data_text))
                    except WebSocketDisconnect:
                        raise
                    except Exception as exc:
                        logging.exception("Error in Service Bus receiving loop: %s", exc)
                    finally:
                        if ctx_token:
                            context.detach(ctx_token)

        except WebSocketDisconnect:
            logging.info("WebSocket: link disconnect: %s", id)
            del self.connections[id]


    async def add_connection(self, websocket: WebSocket, current_user: UserInfo = None) -> str:
        id = str(uuid.uuid4())
        logging.info("WebSocket: new link connection: %s", id)

        await websocket.accept()
        self.connections[id] = ConnectionInfo(websocket=websocket, user_info=current_user)

        return id

    async def send_message(self, dto: BaseModel, id: str=None):
        await self.send_messages([dto], id)

    async def send_messages(self, data: Sequence[BaseModel], id: str=None):
        if id:
            connections = { k:v for k,v in self.connections.items() if k == id }
        else:
            connections = self.connections.copy()

        for id, con in connections.items():
            try:
                logging.info("WebSocket: send messages to connection=%s", id)
                if con.websocket.application_state == WebSocketState.DISCONNECTED:
                    logging.info("WebSocket: connection is disconnected %s, remove from list", id)
                    del self.connections[id]
                    continue
                await self.send_json(con.websocket, [x.model_dump() for x in data])
            except Exception:
                logging.exception("Error with connection!")

    @staticmethod
    async def send_json(connection: WebSocket, data: Any):
        await connection.send_text(json.dumps(data, default=json_default))