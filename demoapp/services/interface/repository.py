from abc import ABC,abstractmethod
from datetime import timedelta
from typing import Iterable
from demoapp.models import Order, ProcessingItem, ProcessingStatus

class OrderRepository(ABC):

    @abstractmethod
    async def create_order(self, order: Order):
        pass

    @abstractmethod
    async def get_order(self, id: str) -> Order:
        pass

    @abstractmethod
    async def get_orders(self, active: bool=False, limit: int=0, offset: int=0, sort: str="created", order: str="asc") -> Iterable[Order]:
        pass

    @abstractmethod
    async def get_orders_count(self) -> int:
        pass

    @abstractmethod
    async def update_order(self, order: Order):
        pass

    @abstractmethod
    async def delete_order(self, id: str):
        pass

    @abstractmethod
    async def delete_all_orders(self):
        pass

    @abstractmethod
    async def close(self):
        pass

class ProcessingRepository(ABC):

    @abstractmethod
    async def create_item(self, item: ProcessingItem):
        pass

    @abstractmethod
    async def get_item(self, id: str) -> ProcessingItem:
        pass

    @abstractmethod
    async def find_item_for_order(self, order_id: str = None) -> ProcessingItem:
        pass

    @abstractmethod
    async def get_items(self, status: ProcessingStatus=None, time_period: timedelta=None) -> Iterable[ProcessingItem]:
        pass

    @abstractmethod
    async def update_item(self, item: ProcessingItem):
        pass

    @abstractmethod
    async def delete_item(self, id: str):
        pass

    @abstractmethod
    async def delete_all_items(self):
        pass

    @abstractmethod
    async def close(self):
        pass

class RepositoryException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class RepositoryAlreadyExistException(RepositoryException):
    def __init__(self, message: str):
        super().__init__(message)

class RepositoryNotFoundException(RepositoryException):
    def __init__(self, message: str):
        super().__init__(message)

