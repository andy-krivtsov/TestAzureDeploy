from __future__ import annotations

import uuid
import random
from datetime import datetime,timedelta, timezone

from typing import Any, Iterable, Optional
from enum import Enum
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field, AnyUrl

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

# ===============================================================================================

class OrderStatus(str, Enum):
    new         = "New"
    created     = "Created"
    processing  = "Processing"
    completed   = "Completed"
    error       = "Error"

class Customer(BaseModel):
    id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer display name")

class ProductItem(BaseModel):
    id: str = Field(..., description="Product item ID")
    name: str = Field(..., description="Item display name")

class OrderListItem(BaseModel):
    item: ProductItem = Field(..., description="Product item")
    count: int = Field(0, description="Count of items")

class Order(BaseModel):
    id: str = Field(..., description="Order ID")
    created: datetime = Field(..., description="Order creation date and time")
    customer: Customer = Field(..., description="Customer")
    items: list[OrderListItem] = Field([], description="Items list")
    due_date: datetime = Field(..., alias="dueDate", description="Order due date")
    status: OrderStatus = Field(OrderStatus.created, description="Order status")

    @staticmethod
    def get_random(customers: list[Customer], items: list[ProductItem]) -> Order:
        return Order(
            id = str(uuid.uuid4()),
            created = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180)),
            customer = random.choice(customers),
            items = [OrderListItem(item=x, count=random.randint(1, 100)) for x in random.choices(items, k=2)],
            dueDate = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 30)),
            status = random.choice(list(OrderStatus))
        )

class PaginationOrdersList(BaseModel):
    total: int = Field(..., description="Total number of orders in store")
    rows: Iterable[Order] = Field( [], description="Orders for page")

class OrderStatusUpdate(BaseModel):
    order_id: str = Field(..., description="Order ID")
    new_status: OrderStatus = Field(..., description="New order status")

class WebsocketConnectInfo(BaseModel):
    url: AnyUrl = Field(..., description="Connection URL for websocket notification connection")