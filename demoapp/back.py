'''
Worker demo application

Application runs in background, and processes requests over ServiceBus
'''
from datetime import datetime, timezone
import os
import logging

from typing import Annotated

from fastapi import Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from demoapp.application import DemoApp
from demoapp.messages_lists import MessageList
from demoapp.settings import AppSettings
from demoapp.models import MessageDTO, ComponentsEnum, MessageStatusListDTO, MessageStatusDTO, StatusTagEnum
from demoapp.dependencies import app_settings, app_templates

class WorkerApp(DemoApp):

    def __init__(self):
        super().__init__(component=ComponentsEnum.db_service, user_auth=False)
        self.received: list[MessageDTO] = []
        self.received_list = MessageList()

    async def app_init(self):
        await super().app_init()
        self.setup_data_receiving()
        self.fastapi.mount("/static", StaticFiles(directory="demoapp/static"), name="static")

    async def process_message(self, message: MessageDTO):
        logging.info(f"Process message: id={message.id}")
        self.received.append(message)

        dto = MessageStatusDTO(
            time=datetime.now(timezone.utc),
            message_id=message.id,
            data=str(message.data))

        dto.status[StatusTagEnum.received] = True
        self.received_list.append(dto)

        await self.queue_service.send_status_message(
            tag=StatusTagEnum.received,
            value=True,
            correlation_id=message.id
        )

app = WorkerApp()
def get_received_list() -> MessageList:
    return app.received_list

# Path functions (API controllers)
@app.fastapi.get("/", response_class=HTMLResponse)
async def get_root(
            request: Request,
            templates: Jinja2Templates = Depends(app_templates)
        ):
    return templates.TemplateResponse("back-main.html.j2", {
        "request": request
    })

@app.fastapi.get("/messages/", response_model=MessageStatusListDTO)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            received_list: MessageList = Depends(get_received_list)
        ) -> MessageStatusListDTO:

    return MessageStatusListDTO(
        version=received_list.version,
        messages=list(received_list.get_after_version(last_version))
    )
