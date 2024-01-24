import asyncio
import logging
import random
import uuid

from demoapp.app.sp import ServiceProvider
from demoapp.services.interface.messaging import MessageService
from demoapp.services.message_base import MessageServiceBase
from demoapp.models import Customer, Order, OrderStatusUpdate, ProcessingStatus, ProductItem
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class MockMessageService(MessageServiceBase):

    def __init__(self, sp: ServiceProvider):
        super().__init__(sp)

    async def send_processing_message(self, order: Order):
        logging.info("Send order for processing id=%s", order.id)
        asyncio.create_task(self._process_order(order))

    async def send_status_message(self, update: OrderStatusUpdate):
        logging.info("Send status update: order_id=%s, new_status: %s", update.order_id, update.new_status)
        asyncio.create_task(self._process_status_update(update))

    async def close(self):
        super().close()

class MockFrontService:
    def __init__(self, messaging_service: MessageService, minDelay: int=20, maxDelay: int=40):
        self.messaging_service = messaging_service
        self.minDelay = minDelay
        self.maxDelay = maxDelay

        messaging_service.subscribe_status_messages(self.process_status)

        self._background_task = asyncio.create_task(self.background_worker())

    async def process_status(self, update: OrderStatusUpdate, sp: ServiceProvider):
        logging.info("Generator: received status update for order %s, new status: %s", update.order_id, update.new_status)

    async def background_worker(self):
        try:
            customers = [Customer(id=str(uuid.uuid4()), name=f"Customer Name #{i}") for i in range(20)]
            prodItems = [ProductItem(id=str(uuid.uuid4()), name=f"Product Item #{i}") for i in range(20)]

            while True:
                order = Order.get_random(customers, prodItems, datetime.now(timezone.utc))
                logging.info("Generator: send new order id = %s", order.id)

                await self.messaging_service.send_processing_message(order)

                delay = random.randint(self.minDelay, self.maxDelay)
                logging.info("Generator: sleep next %s seconds", delay)
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logging.info("Orders generation background task is canceled!")

    async def close(self):
        self._background_task.cancel()


class MockProcessingItem(BaseModel):
    order: Order = Field(..., description="Queue item")
    processing_time: int = Field(0, description="Processing time in seconds")

class MockProcessingService:
    def __init__(self, messaging_service: MessageService):
        self.messaging_service = messaging_service
        messaging_service.subscribe_processing_messages(self.process_order)

    async def process_order(self, order: Order, sp: ServiceProvider):
        await asyncio.sleep(1)

        delay = random.randint(5, 30)
        logging.info("Start mock processing of order: %s, processing time = %s seconds", order.id, delay)

        item = MockProcessingItem(order=order, processing_time=delay)

        await self.messaging_service.send_status_message(OrderStatusUpdate(
            order_id=order.id,
            new_status=ProcessingStatus.processing
        ))

        asyncio.create_task(self.background_order_processing(item))

    async def background_order_processing(self, item: MockProcessingItem):
        await asyncio.sleep(item.processing_time)

        logging.info("Order processing finished: id=%s", item.order.id)

        await self.messaging_service.send_status_message(OrderStatusUpdate(
            order_id=item.order.id,
            new_status=ProcessingStatus.completed
        ))

    async def close(self):
        pass
