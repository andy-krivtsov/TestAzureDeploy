from demoapp.services.interface.messaging import MessageService, OrderProcessor, OrderStatusProcessor
from demoapp.app.sp import ServiceProvider
from demoapp.models import Order, OrderStatusUpdate

class MessageServiceBase(MessageService):

    def __init__(self, sp: ServiceProvider):
        super().__init__()
        self._sp = sp
        self._order_processors: list[OrderProcessor] = []
        self._status_processors: list[OrderStatusProcessor] = []

    def subscribe_processing_messages(self, processor: OrderProcessor):
        self._order_processors.append(processor)

    def unsubscribe_processing_messages(self, processor: OrderProcessor):
        try:
            self._order_processors.remove(processor)
        except ValueError:
            return

    def subscribe_status_messages(self, processor: OrderStatusProcessor):
        self._status_processors.append(processor)

    def unsubscribe_status_messages(self, processor: OrderStatusProcessor):
        try:
            self._status_processors.remove(processor)
        except ValueError:
            return

    async def _process_order(self, order: Order):
        for f in self._order_processors:
            await f(order, self._sp)

    async def _process_status_update(self, update: OrderStatusUpdate):
        for f in self._status_processors:
            await f(update, self._sp)

    async def close(self):
        await super().close()
        self._order_processors.clear()
        self._status_processors.clear()


