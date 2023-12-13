'''
Worker demo application

Application runs in background, and processes requests over ServiceBus
'''
from asyncio import Task, create_task
import logging

from typing import Annotated, Any

from fastapi import FastAPI, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from demoapp.application import AppBuilder, ServiceProvider
from demoapp.messages_lists import MessageList
from demoapp.servicebus import QueueService
from demoapp.database import DbService
from demoapp.settings import AppSettings
from demoapp.models import MessageDTO, ComponentsEnum, MessageStatusListDTO, MessageStatusDTO, StatusTagEnum
from demoapp.dependencies import app_templates


data_receiver_task: Task[Any] = None

received_list = MessageList()
def get_received_list() -> MessageList:
    return received_list

async def process_message(message: MessageDTO):
    try:
        logging.info(f"Process message: id={message.id}")
        sp = ServiceProvider()
        received_list = get_received_list()

        dto = MessageStatusDTO.fromMessage(message)
        dto.set_status(StatusTagEnum.received, True)
        received_list.append(dto)

        db: DbService = sp.get_service(DbService)
        await db.write_message(message)

        queue: QueueService = sp.get_service(QueueService)
        await queue.send_status_message(
            tag=StatusTagEnum.db,
            value=True,
            correlation_id=message.id
        )

        received_list.update_status(message.id, StatusTagEnum.db, True)
    except Exception as exc:
        logging.error(f"Exception in message processing: {exc}", stack_info=True)

async def app_init(app: FastAPI, sp: ServiceProvider):
    global data_receiver_task
    settings: AppSettings = sp.get_service(AppSettings)

    queue: QueueService = QueueService(settings, app.state.component)
    sp.register(QueueService, queue)

    sp.register(DbService, DbService(settings))

    data_receiver_task = create_task(queue.receive_messages(process_message))


app = AppBuilder(ComponentsEnum.db_service)\
        .with_settings(AppSettings()) \
        .with_cors() \
        .with_static() \
        .with_msal() \
        .with_init(app_init) \
        .build()


# Path functions (API controllers)
@app.get("/", response_class=HTMLResponse)
async def get_root(
            request: Request,
            templates: Jinja2Templates = Depends(app_templates)
        ):
    return templates.TemplateResponse("back-main.html.j2", {
        "request": request
    })

@app.get("/messages/", response_model=MessageStatusListDTO)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            received_list: MessageList = Depends(get_received_list)
        ) -> MessageStatusListDTO:

    return MessageStatusListDTO(
        version=received_list.version,
        messages=list(received_list.get_after_version(last_version))
    )
