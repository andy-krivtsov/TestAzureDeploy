import json
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field

class Message(BaseModel):
    id: Optional[str] = Field(None, description="Message id")
    correlation_id: Optional[str] = Field(None, description="Corelation ID")
    data: Any = Field({}, description="Message content")


class MessageStatusData(BaseModel):
    source: str = Field("def_source", description="Source of the status message")
    tag: str = Field("def_tag", description="Status tag")
    value: bool = Field(True, description="Status value")

class StatusMessage(Message):
    data: MessageStatusData = Field(..., description="Message content")


def test_func(m: Message):
    print(f"Type: {type(m)}")
    print(m.model_dump_json(indent=2))


m1 = Message(id="1", data="Test data 01")
test_func(m1)
d1 = m1.model_dump_json()

m2 = StatusMessage(id="2", data = MessageStatusData(source="source",tag="tag",value=False))
test_func(m2)
d2 = m2.model_dump_json()

m11 = Message.model_validate_json(d1)
test_func(m11)

m21 = Message.model_validate_json(d2)
test_func(m21)

m32 = StatusMessage.model_validate_json(m21.model_dump_json())
test_func(m32)

m33 = StatusMessage.model_validate(m21.model_dump())
test_func(m32)
