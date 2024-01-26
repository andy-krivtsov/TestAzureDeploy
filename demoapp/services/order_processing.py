import asyncio
import logging
from datetime import datetime, timedelta, timezone

from demoapp.app.sp import ServiceProvider
from demoapp.models import ProcessingItem, OrderStatusUpdate, ProcessingStatus
from demoapp.services import ProcessingRepository, MessageService, WebsocketService

class OrderProcessor:
    def __init__(self, item: ProcessingItem, sp: ServiceProvider):
        self.item = item
        self.repository: ProcessingRepository = sp.get_service(ProcessingRepository)
        self.message_service: MessageService = sp.get_service(MessageService)
        self.websocket_service: WebsocketService = sp.get_service(WebsocketService)

    async def process(self):
        try:
            self.item.status = ProcessingStatus.processing
            self.item.started = datetime.now(timezone.utc)
            await self.repository.update_item(self.item)
            await self.send_status_update()

            await asyncio.sleep(self.item.processing_time)

            d = datetime.now(timezone.utc)
            logging.info("Order processing is finished, id = %s, order = %s", self.item.id, self.item.order.id)

            self.item.finished = d
            self.item.status = ProcessingStatus.completed
            await self.repository.update_item(self.item)

            await self.send_status_update()
        except Exception:
            logging.exception("Error in processing order: %s", self.item.order.id)
            self.item.status = ProcessingStatus.error
            await self.send_status_update()
            raise Exception("Error in processing item")

    async def error(self):
        self.item.status = ProcessingStatus.error
        await self.repository.update_item(self.item)

    async def create_item(self):
        try:
            await self.repository.create_item(self.item)
        except Exception:
            logging.exception("Error in creating processing item in repository: order_id: %s", self.item.order.id)
            self.item.status = ProcessingStatus.error
            await self.send_status_update()
            raise Exception("Error in creating processing item")

    async def send_status_update(self):
        await self.message_service.send_status_message(OrderStatusUpdate(
            order_id=self.item.order.id,
            new_status=self.item.status
        ))

        await self.websocket_service.send_client_processing_update([ self.item ])

class OrderProcessingRecovery:
    def __init__(self, sp: ServiceProvider):
        self.sp = sp
        self.repository: ProcessingRepository = sp.get_service(ProcessingRepository)

    async def mark_recovery_items(self, delay_sec: int = 3):
        await asyncio.sleep(delay_sec)

        logging.info("Recovery: check non-completed items")
        items = await self.repository.get_items(status=ProcessingStatus.processing)

        check_time = datetime.now(timezone.utc) - timedelta(hours=3)
        for item in items:
            if check_time > item.created:
                item.status = ProcessingStatus.error
            else:
                item.status = ProcessingStatus.recovery

            logging.info("Recovery: set item id=%s to '%s' status", item.id, item.status.value)
            await self.repository.update_item(item)

        await self.restart_processing_items()

    async def restart_processing_items(self, delay_sec: int = 15):
        await asyncio.sleep(delay_sec)

        items = await self.repository.get_items(status=ProcessingStatus.recovery)

        for item in items:
            processor = OrderProcessor(item, self.sp)
            logging.info("Recovery: restart item id=%s", item.id)
            asyncio.create_task(processor.process())
            await asyncio.sleep(2)

