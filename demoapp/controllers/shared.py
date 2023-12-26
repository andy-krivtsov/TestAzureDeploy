from typing import Any
from demoapp.models import MessageViewDTO
from demoapp.services.websocket import WebSocketManager


# Message list update handler: send update to the fronted via WebSocket
# Signature for library 'async_signals'
class ListUpdateHandler:
    def __init__(self, con_manager: WebSocketManager):
        self.con_manager = con_manager

    async def on_update(self, sender: Any, message_info: MessageViewDTO, **kwargs):
        await self.con_manager.send_message(message_info)
