import asyncio
from collections import deque
import logging
import random

from demoapp.app.sp import ServiceProvider
from demoapp.services.message_service import MessageServiceBase
from demoapp.models import Order, OrderStatus, OrderStatusUpdate
from pydantic import BaseModel, Field
from datetime import datetime,timedelta, timezone


class ProcessingItem(BaseModel):
    item: Order = Field(..., description="Queue item")
    finish_time: datetime = Field(datetime.now(timezone.utc), description="Item finish processing time")

class MockMessageService(MessageServiceBase):

    def __init__(self, sp: ServiceProvider):
        super().__init__(sp)

        self._processing_list: list[ProcessingItem] = list()
        self._status_queue: deque[OrderStatusUpdate] = deque()

        self._background_process_task: asyncio.Task = asyncio.create_task(self.process_items())
        self._background_status_task: asyncio.Task = asyncio.create_task(self.process_status_items())


    async def send_processing_message(self, order: Order):
        delay = random.randint(1, 30)
        logging.info("Send order for processing id=%s, delay=%s sec", order.id, delay)
        self._processing_list.append(ProcessingItem(
            item=order,
            finish_time=datetime.now(timezone.utc) + timedelta(seconds=delay)
        ))
        await self.send_status_message(OrderStatusUpdate(
            order_id=order.id,
            new_status=OrderStatus.processing
        ))

    async def send_status_message(self, update: OrderStatusUpdate):
        logging.info("Send status update: order_id=%s, new_status: %s", update.order_id, update.new_status)
        self._status_queue.append(update)


    async def process_items(self):
        try:
            while True:
                logging.debug("Orders processing queue task is running")
                d = datetime.now(timezone.utc)

                finished = [x for x in self._processing_list if x.finish_time <= d]

                for queue_item in finished:
                    logging.info("Order processing finished: id=%s", queue_item.item.id)
                    self._processing_list.remove(queue_item)

                    await self._process_order(queue_item.item)

                    await self.send_status_message(OrderStatusUpdate(
                        order_id=queue_item.item.id,
                        new_status=OrderStatus.completed
                    ))

                await asyncio.sleep(2)
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

                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logging.info("Status processing queue task is canceled!")


    async def close(self):
        self._background_process_task.cancel()
        self._background_status_task.cancel()
        super().close()