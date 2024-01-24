from abc import ABC,abstractmethod
from typing import Awaitable, TypeAlias, Callable

from demoapp.app.sp import ServiceProvider
from demoapp.models import Order, OrderStatusUpdate

OrderProcessor: TypeAlias = Callable[[Order, ServiceProvider], Awaitable]
OrderStatusProcessor: TypeAlias = Callable[[OrderStatusUpdate, ServiceProvider], Awaitable]

class MessageService(ABC):

    @abstractmethod
    async def send_processing_message(self, order: Order):
        pass

    @abstractmethod
    async def send_status_message(self, update: OrderStatusUpdate):
        pass

    @abstractmethod
    def subscribe_processing_messages(self, processor: OrderProcessor):
        pass

    @abstractmethod
    def unsubscribe_processing_messages(self, processor: OrderProcessor):
        pass

    @abstractmethod
    def subscribe_status_messages(self, processor: OrderStatusProcessor):
        pass

    @abstractmethod
    def unsubscribe_status_messages(self, processor: OrderStatusProcessor):
        pass

    @abstractmethod
    async def close(self):
        pass
