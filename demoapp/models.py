from __future__ import annotations

from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field

def json_default(obj: Any) -> Any:
    return obj.isoformat() if isinstance(obj, datetime) or isinstance(obj, date) else None

class StatusTagEnum(str, Enum):
    sent     = "sent"
    received = "received"
    db       = "db"
    storage  = "storage"

class ComponentsEnum(str, Enum):
    front_service = "front-service"
    db_service = "db-service"
    stor_service = "stor-service"

class Message(BaseModel):
    id: Optional[str] = Field(None, description="Message id")
    correlation_id: Optional[str] = Field(None, description="Corelation ID")
    data: Any = Field(None, description="Message content")

class StatusMessage(Message):
    data: MessageStatusData = Field(..., description="Status information")

class MessageStatusData(BaseModel):
    source: ComponentsEnum = Field(..., description="Source of the status message")
    tag: StatusTagEnum = Field(..., description="Status tag")
    value: bool = Field(..., description="Status value")

class MessageViewDTO(BaseModel):
    version: int = -1
    time: datetime
    message: Message
    status: dict[StatusTagEnum, bool] = {}

    def set_status(self, tag: StatusTagEnum, value: bool):
        self.status[tag] = value

    def is_completed(self) -> bool:
        return (self.status.get(StatusTagEnum.sent, False) and
                self.status.get(StatusTagEnum.db, False) and
                self.status.get(StatusTagEnum.storage, False))

    @staticmethod
    def fromMessage(message: Message, status: dict[StatusTagEnum, bool] = {}, version: int = -1) -> MessageViewDTO:
        dto = MessageViewDTO(
            version=version,
            time=datetime.now(timezone.utc),
            message=message)

        for k, v in status.items():
            dto.set_status(k, v)

        return dto


class MessageViewList(BaseModel):
    version: int = 0
    messages: list[MessageViewDTO] = []
