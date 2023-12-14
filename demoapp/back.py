'''
Worker demo application

Application runs in background, and processes requests over ServiceBus
'''
from asyncio import Task, create_task
import logging

from typing import Annotated, Any

from fastapi import FastAPI, Query, Request, Depends, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from demoapp.application import AppBuilder, ServiceProvider
from demoapp.messages_lists import MessageList
from demoapp.servicebus import QueueService
from demoapp.database import DbService
from demoapp.settings import AppSettings
from demoapp.models import MessageDTO, ComponentsEnum, MessageStatusListDTO, MessageStatusDTO, StatusTagEnum
from demoapp.dependencies import app_templates
from demoapp.websocket import WebSocketLinkManager

# Received message list
received_list = MessageList()
def get_received_list() -> MessageList:
    return received_list

# WebSocket management and event handlers
async def new_connect_handler(connection: WebSocket):
    logging.info("WebSocket: sent complete list to the new connection")
    await WebSocketLinkManager.send_json(
        connection,
        [ x.model_dump() for x in received_list.messages ]
    )

view_connections = WebSocketLinkManager(on_connection=new_connect_handler)
def get_view_connections() -> WebSocketLinkManager:
    return view_connections

# Received list update event handler (sent event to websocket)
async def received_list_update_handler(sender: Any, message_info: MessageStatusDTO, **kwargs):
    await view_connections.send_message(message_info)

received_list.on_change_connect(received_list_update_handler)

# Incoming Service Bus  messages processing
async def process_message(message: MessageDTO):
    try:
        logging.info("Process data message: id=%s", message.id)
        sp = ServiceProvider()
        received_list = get_received_list()

        dto = MessageStatusDTO.fromMessage(message)
        dto.set_status(StatusTagEnum.received, True)
        await received_list.append(dto)

        db: DbService = sp.get_service(DbService)
        await db.write_message(message)

        queue: QueueService = sp.get_service(QueueService)
        await queue.send_status_message(
            tag=StatusTagEnum.db,
            value=True,
            correlation_id=message.id
        )

        await received_list.update_status(message.id, StatusTagEnum.db, True)
    except Exception:
        logging.exception("Exception in message processing! id=%s", message.id)

#  Application initialization and FastAPI object
data_receiver_task: Task[Any] = None
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


@app.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            view_connections: WebSocketLinkManager = Depends(get_view_connections)
        ):
    await view_connections.new_connection(websocket)
