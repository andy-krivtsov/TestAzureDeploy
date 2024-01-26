from __future__ import annotations

import uuid
import random
from datetime import datetime,timedelta, timezone

from typing import Any, Iterable, Optional
from enum import Enum
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field, AnyUrl, ConfigDict
from pydantic.alias_generators import to_camel

class OrderStatus(str, Enum):
    new         = "New"
    processing  = "Processing"
    completed   = "Completed"
    error       = "Error"

class ProcessingStatus(str, Enum):
    new         = "New"
    processing  = "Processing"
    completed   = "Completed"
    recovery    = "Recovery"
    error       = "Error"

class Customer(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer display name")

class ProductItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str = Field(..., description="Product item ID")
    name: str = Field(..., description="Item display name")

class OrderListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    item: ProductItem = Field(..., description="Product item")
    count: int = Field(0, description="Count of items")

class Order(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str = Field(..., description="Order ID")
    created: datetime = Field(..., description="Order creation date and time")
    customer: Customer = Field(..., description="Customer")
    items: list[OrderListItem] = Field([], description="Items list")
    due_date: datetime = Field(..., description="Order due date")
    status: OrderStatus = Field(OrderStatus.new, description="Order status")

    @staticmethod
    def get_random(customers: list[Customer], items: list[ProductItem], created: datetime = None) -> Order:
        if not created:
            created = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))

        return Order(
            id = str(uuid.uuid4()),
            created = created,
            customer = random.choice(customers),
            items = [OrderListItem(item=x, count=random.randint(1, 100)) for x in random.choices(items, k=2)],
            due_date = created + timedelta(days=random.randint(1, 30)),
            status = random.choice(list(OrderStatus))
        )

class PaginationOrdersList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    total: int = Field(..., description="Total number of orders in store")
    rows: Iterable[Order] = Field( [], description="Orders for page")

class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    order_id: str = Field(..., description="Order ID")
    new_status: ProcessingStatus = Field(ProcessingStatus.new, description="New order status")

class WebsocketConnectInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    url: AnyUrl = Field(..., description="Connection URL for websocket notification connection")
    protocol: str =  Field("", description="WebSocket subprotocol")

class ProcessingItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str = Field(..., description="Item ID")
    created: datetime = Field(..., description="Item creation date and time")
    started: Optional[datetime] = Field(None, description="Item processing start time")
    order: Order = Field(..., description="Processing order")
    processing_time: int = Field(0, description="Time for order processing in seconds")
    finished: Optional[datetime] = Field(None, description="Item processing finishing date and time")
    status: ProcessingStatus = Field(ProcessingStatus.processing, description="Item status")

class FrontendSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    login_url: str = Field(..., description="Login URL")
    logout_url: str = Field(..., description="Logout URL")


