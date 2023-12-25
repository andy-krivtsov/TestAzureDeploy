import asyncio
from typing import Any
import fastapi
from demoapp.app import Application
from demoapp.models import ComponentsEnum
from demoapp.services.messagelist import MessageList
from demoapp.services.servicebus import MessagingService
from demoapp.controllers.front import process_status_message

class FrontApp(Application):

    def __init__(self):
        super().__init__(component=ComponentsEnum.front_service)

        self._sent_list = MessageList()

        self._messaging: MessagingService = None
        self._status_receiver_task: asyncio.Task[Any] = None

    async def app_init(self, app: fastapi.FastAPI):
        self._messaging = MessagingService(self.settings, self.component)
        status_receiver_task = asyncio.create_task(
            self._messaging.receive_messages(process_status_message,True)
        )


    async def app_shutdown(self, app: fastapi.FastAPI):
        if self._status_receiver_task:
            self._status_receiver_task.cancel()

        await  self._messaging.close()

    @property
    def messaging(self):
        return self._messaging

    @property
    def sent_list(self):
        return self._sent_list
