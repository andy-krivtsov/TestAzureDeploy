from typing import Iterable
from demoapp.models import StatusTagEnum, MessageStatusDTO

class MessageList:
    def __init__(self):
        self.messages: list[MessageStatusDTO] = []
        self.version: int = 0

    def append(self, msg_info: MessageStatusDTO):
        self.version += 1
        msg_info.version = self.version
        self.messages.append(msg_info)

    def get_by_id(self, id: str) -> MessageStatusDTO:
        return next((x for x in self.messages if x.message_id == id), None)

    def get_after_version(self, last_version: int = -1) -> Iterable[MessageStatusDTO]:
        return (x for x in self.messages if x.version > last_version)

    def update_status(self, id: str, tag: StatusTagEnum, value: bool):
        msg_info = self.get_by_id(id)
        if msg_info:
            self.version += 1
            msg_info.version = self.version
            msg_info.status[tag] = value

