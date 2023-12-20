from typing import Any, Awaitable, Callable, Optional
import uuid
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
from fastapi_msal import UserInfo
from pydantic import BaseModel
from demoapp.models import json_default
from opentelemetry.trace import get_tracer, SpanKind, get_current_span, Link
from opentelemetry.context import Context
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry import baggage
from opentelemetry import context

tracer = get_tracer(__name__)

class WebSocketManager:
    def __init__(
            self,
            on_connection: Callable[[WebSocket, Optional[UserInfo]], Awaitable[None]] = None,
            on_received: Callable[[Any], Awaitable[None]] = None):
        self.connections: dict[str, WebSocket] = {}
        self.on_connection = on_connection
        self.on_received = on_received

    async def new_connection(self, websocket: WebSocket, current_user: UserInfo = None):
        id = str(uuid.uuid4())
        logging.info("WebSocket: new link connection: %s", id)

        await websocket.accept()
        self.connections[id] = websocket

        if self.on_connection:
            await self.on_connection(websocket, current_user)

        try:
            while True:
                data_text = await websocket.receive_text()
                if self.on_received:
                    ctx_token = None
                    try:
                        with tracer.start_as_current_span(
                                name="websocket.receive_frontend_message",
                                context=Context(),
                                kind=SpanKind.SERVER,
                                record_exception=True,
                                attributes={
                                    SpanAttributes.ENDUSER_ID: current_user.preferred_username,
                                    "demoapp.websocket_id": id
                                }):
                            ctx = baggage.set_baggage(SpanAttributes.ENDUSER_ID, current_user.preferred_username)
                            ctx_token = context.attach(ctx)

                            await self.on_received(json.loads(data_text))
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

    async def send_message(self, dto: BaseModel):
        await self.send_messages([dto])

    async def send_messages(self, data: list[BaseModel]):
        for id, con in self.connections.items():
            logging.info("WebSocket: send messages to connection=%s", id)
            await self.send_json(con, [x.model_dump() for x in data])

    @staticmethod
    async def send_json(connection: WebSocket, data: Any):
        await connection.send_text(json.dumps(data, default=json_default))