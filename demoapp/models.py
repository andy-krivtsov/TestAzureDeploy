from __future__ import annotations

import json
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field
from azure.servicebus import ServiceBusMessage, ServiceBusReceivedMessage

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

class MessageDTO(BaseModel):
    id: Optional[str] = Field(None, description="Message id")
    correlation_id: Optional[str] = Field(None, description="Corelation ID")
    data: Any = Field(None, description="Message content")

    def toServiceBusMessage(self) -> ServiceBusMessage:
        msg_body: str = ""
        if self.data:
            if isinstance(self.data, BaseModel):
                msg_body = self.data.model_dump_json()
            else:
                msg_body = json.dumps(self.data)

        return ServiceBusMessage(
            body=msg_body,
            content_type="application/json",
            message_id=self.id,
            correlation_id=self.correlation_id
        )

    @staticmethod
    def fromServiceBusMessage(msg: ServiceBusReceivedMessage) -> MessageDTO:
        return MessageDTO(
            id=msg.message_id,
            correlation_id=msg.correlation_id,
            data=json.loads(next(msg.body).decode('utf-8'))
        )

class StatusData(BaseModel):
    source: ComponentsEnum = Field(..., description="Source of the status message")
    tag: StatusTagEnum = Field(..., description="Status tag")
    value: bool = Field(..., description="Status value")


class MessageStatusDTO(BaseModel):
    version: int = -1
    time: datetime
    message: MessageDTO
    status: dict[StatusTagEnum, bool] = {}

    def set_status(self, tag: StatusTagEnum, value: bool):
        self.status[tag] = value

    @staticmethod
    def fromMessage(message: MessageDTO, version: int = -1) -> MessageStatusDTO:
        return MessageStatusDTO(
            version=version,
            time=datetime.now(timezone.utc),
            message=message)


class MessageStatusListDTO(BaseModel):
    version: int = 0
    messages: list[MessageStatusDTO] = []
