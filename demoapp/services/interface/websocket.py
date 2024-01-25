from abc import ABC,abstractmethod
from fastapi import FastAPI

from demoapp.models import Order, WebsocketConnectInfo, ProcessingItem
from demoapp.services import AppSettings

class WebsocketService(ABC):

    def __init__(self, app: FastAPI, settings: AppSettings):
        self._app = app
        self._settings = settings

    @abstractmethod
    async def get_client_connection_info(self, user_id: str) -> WebsocketConnectInfo:
        pass

    @abstractmethod
    async def send_client_order_update(self, orders: list[Order]):
        pass

    @abstractmethod
    async def send_client_processing_update(self, items: list[ProcessingItem]):
        pass

    @abstractmethod
    async def close(self):
        pass
