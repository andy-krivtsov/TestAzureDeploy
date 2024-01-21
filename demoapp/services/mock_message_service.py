import asyncio
from collections import deque
import logging
import random
import uuid

from demoapp.app.sp import ServiceProvider
from demoapp.services.message_service import MessageServiceBase, MessageService
from demoapp.models import Customer, Order, OrderStatus, OrderStatusUpdate, ProcessingStatus, ProductItem
from pydantic import BaseModel, Field
from datetime import datetime,timedelta, timezone

class MockMessageService(MessageServiceBase):

    def __init__(self, sp: ServiceProvider):
        super().__init__(sp)

        self._processing_queue: deque[Order] = deque()
        self._status_queue: deque[OrderStatusUpdate] = deque()

        self._background_process_task: asyncio.Task = asyncio.create_task(self.process_items())
        self._background_status_task: asyncio.Task = asyncio.create_task(self.process_status_items())


    async def send_processing_message(self, order: Order):
        logging.info("Send order for processing id=%s", order.id)
        self._processing_queue.append(order)


    async def send_status_message(self, update: OrderStatusUpdate):
        logging.info("Send status update: order_id=%s, new_status: %s", update.order_id, update.new_status)
        self._status_queue.append(update)


    async def process_items(self):
        try:
            while True:
                logging.debug("Orders processing queue task is running")

                while len(self._processing_queue):
                    try:
                        queue_item = self._processing_queue.popleft()
                        logging.info("New order message processing: id=%s", queue_item.id)
                        await self._process_order(queue_item)
                    except Exception:
                        logging.exception("Error during order message processing")

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Orders processing queue task is canceled!")


    async def process_status_items(self):
        try:
            while True:
                logging.debug("Status processing queue task is running")

                while len(self._status_queue):
                    try:
                        queue_item = self._status_queue.popleft()
                        logging.info("New status message processing: id=%s, status=%s", queue_item.order_id, queue_item.new_status)
                        await self._process_status_update(queue_item)
                    except Exception:
                        logging.exception("Error during status message processing")

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Status processing queue task is canceled!")


    async def close(self):
        self._background_process_task.cancel()
        self._background_status_task.cancel()
        super().close()

class MockFrontService:
    def __init__(self, messaging_service: MessageService):
        self.messaging_service = messaging_service

        messaging_service.subscribe_status_messages(self.process_status)

        self._background_task: asyncio.Task = asyncio.create_task(self.background_worker())

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

                delay = random.randint(2, 8)
                logging.info("Generator: sleep next %s seconds", delay)
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logging.info("Orders generation background task is canceled!")

    async def close(self):
        self._background_task.cancel()


class MockProcessingItem(BaseModel):
    item: Order = Field(..., description="Queue item")
    finish_time: datetime = Field(datetime.now(timezone.utc), description="Item finish processing time")


class MockProcessingService:
    def __init__(self, messaging_service: MessageService):
        self.messaging_service = messaging_service
        self._items: list[MockProcessingItem] = []

        messaging_service.subscribe_processing_messages(self.process_order)

        self._background_task: asyncio.Task = asyncio.create_task(self.background_processing())

    async def process_order(self, order: Order, sp: ServiceProvider):
        await asyncio.sleep(1)

        delay = random.randint(5, 30)
        logging.info("Start mock processing of order: %s, processing time = %s seconds", order.id, delay)

        self._items.append(MockProcessingItem(
            item=order,
            finish_time=datetime.now(timezone.utc) + timedelta(seconds=delay)
        ))

        await self.messaging_service.send_status_message(OrderStatusUpdate(
            order_id=order.id,
            new_status=ProcessingStatus.processing
        ))

    async def background_processing(self):
        try:
            while True:
                logging.debug("Orders processing background task is running")
                d = datetime.now(timezone.utc)

                finished = [x for x in self._items if x.finish_time <= d]

                for queue_item in finished:
                    logging.info("Order processing finished: id=%s", queue_item.item.id)
                    self._items.remove(queue_item)

                    await self.messaging_service.send_status_message(OrderStatusUpdate(
                        order_id=queue_item.item.id,
                        new_status=ProcessingStatus.completed
                    ))

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Orders processing background task is canceled!")

    async def close(self):
        self._background_task.cancel()
