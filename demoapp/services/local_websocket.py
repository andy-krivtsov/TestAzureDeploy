import logging
import uuid
from fastapi import FastAPI, APIRouter, WebSocket, Depends, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from fastapi.encoders import jsonable_encoder

from demoapp.services.interface.websocket import WebsocketService
from demoapp.models import Order, ProcessingItem, WebsocketConnectInfo
from demoapp.services import AppSettings
from demoapp import dep
from fastapi_msal.models import UserInfo
from pydantic import AnyUrl

router = APIRouter()

ws_connections: dict[str, WebSocket] = {}

@router.websocket("/notifications/feed")
async def notify_websocket(
            websocket: WebSocket,
            current_user: UserInfo = Depends(dep.optional_auth_scheme)
        ):

    id = str(uuid.uuid4())
    logging.info("WebSocket: new link connection: %s", id)

    await websocket.accept()
    ws_connections[id] = websocket

    # Start received messages
    try:
         while True:
            data_text = await websocket.receive_text()
            logging.info("WebSocket: received from client: %s", data_text)

    except WebSocketDisconnect:
        logging.info("WebSocket: link disconnect: %s", id)
        del ws_connections[id]

class LocalWebsocketService(WebsocketService):

    def __init__(self, app: FastAPI, settings: AppSettings):
        super().__init__(app, settings)
        app.include_router(router)

    async def get_client_connection_info(self, user_id: str) -> WebsocketConnectInfo:
        pub_url = AnyUrl(self._settings.auth_public_url)

        ws_scheme = "wss" if pub_url.scheme == "https" else "ws"
        ws_port = f":{pub_url.port}" if pub_url.port else ""
        ws_url = AnyUrl(f"{ws_scheme}://{pub_url.host}{ws_port}/notifications/feed")

        return WebsocketConnectInfo(url=ws_url)

    async def send_client_order_update(self, orders: list[Order]):
        await self._send_impl(orders)

    async def send_client_processing_update(self, items: list[ProcessingItem]):
        await self._send_impl(items)

    async def _send_impl(self, data: list):
        for id, con in ws_connections.items():
            try:
                logging.info("WebSocket: send messages to connection=%s", id)
                if con.application_state == WebSocketState.DISCONNECTED:
                    logging.info("WebSocket: connection is disconnected %s, remove from list", id)
                    del ws_connections[id]
                    continue

                await con.send_json(jsonable_encoder(data))
            except Exception:
                logging.exception("Error with connection!")

    async def close(self):
        for id, con in ws_connections.items():
            await con.close()
