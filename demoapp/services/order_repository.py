from abc import ABC,abstractmethod
from typing import Iterable
from demoapp.models import Order

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

class OrderRepositoryException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class OrderAlreadyExistException(OrderRepositoryException):
    def __init__(self, message: str):
        super().__init__(message)

class OrderNotFoundException(OrderRepositoryException):
    def __init__(self, message: str):
        super().__init__(message)


