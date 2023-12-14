from typing import Callable, Iterable
from async_signals import Signal
from demoapp.models import StatusTagEnum, MessageStatusDTO

class MessageList:
    def __init__(self):
        self.messages: list[MessageStatusDTO] = []
        self.version: int = 0
        self._onchange = Signal()

    def on_change_connect(self, receiver: Callable):
        self._onchange.connect(receiver)

    def on_change_disconnect(self, receiver: Callable):
        self._onchange.disconnect(receiver)

    async def on_change(self, message_info: MessageStatusDTO):
        await self._onchange.send(sender=self, message_info=message_info)

    async def append(self, message_info: MessageStatusDTO):
        self.version += 1
        message_info.version = self.version
        self.messages.append(message_info)
        await self.on_change(message_info)

    def get_by_id(self, id: str) -> MessageStatusDTO:
        return next((x for x in self.messages if x.message.id == id), None)

    def get_after_version(self, last_version: int = -1) -> Iterable[MessageStatusDTO]:
        return (x for x in self.messages if x.version > last_version)

    async def update_status(self, id: str, tag: StatusTagEnum, value: bool) -> MessageStatusDTO:
        message_info = self.get_by_id(id)
        if message_info:
            self.version += 1
            message_info.version = self.version
            message_info.status[tag] = value
            await self.on_change(message_info)

        return message_info

