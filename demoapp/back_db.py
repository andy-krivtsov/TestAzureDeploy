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
from demoapp.services.messagelist import MessageList
from demoapp.services.servicebus import MessagingService
from demoapp.services.cosmosdb import DatabaseService
from demoapp.settings import AppSettings
from demoapp.models import Message, ComponentsEnum, MessageViewList, MessageViewDTO, StatusTagEnum
from demoapp.services.dependencies import app_templates
from demoapp.services.websocket import WebSocketManager

# Received message list
received_list = MessageList()
def get_received_list() -> MessageList:
    return received_list

# WebSocket management and event handlers
async def new_connect_handler(connection: WebSocket):
    logging.info("WebSocket: sent complete list to the new connection")
    await WebSocketManager.send_json(
        connection,
        [ x.model_dump() for x in received_list.messages ]
    )

view_connections = WebSocketManager(on_connection=new_connect_handler)
def get_view_connections() -> WebSocketManager:
    return view_connections

# Received list update event handler (sent event to websocket)
async def received_list_update_handler(sender: Any, message_info: MessageViewDTO, **kwargs):
    await view_connections.send_message(message_info)

received_list.on_change_connect(received_list_update_handler)

# Incoming Service Bus  messages processing
async def process_message(message: Message):
    try:
        logging.info("Process data message: id=%s", message.id)
        sp = ServiceProvider()
        received_list = get_received_list()

        dto = MessageViewDTO.fromMessage(message)
        dto.set_status(StatusTagEnum.received, True)
        await received_list.append(dto)

        db_srv: DatabaseService = sp.get_service(DatabaseService)
        await db_srv.write_message(message)

        msg_srv: MessagingService = sp.get_service(MessagingService)
        await msg_srv.send_status_message(
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

    msg_srv: MessagingService = MessagingService(settings, app.state.component)
    sp.register(MessagingService, msg_srv)

    sp.register(DatabaseService, DatabaseService(settings))

    data_receiver_task = create_task(msg_srv.receive_messages(process_message))

async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    global data_receiver_task

    msg_srv: MessagingService = sp.get_service(MessagingService)
    data_receiver_task.cancel()
    await msg_srv.close()

    db_srv: DatabaseService = sp.get_service(DatabaseService)
    await db_srv.close()


app = AppBuilder(ComponentsEnum.db_service)\
        .with_settings(AppSettings()) \
        .with_cors() \
        .with_static() \
        .with_msal() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .build()


# Path functions (API controllers)
@app.get("/", response_class=HTMLResponse)
async def get_root(
            request: Request,
            templates: Jinja2Templates = Depends(app_templates)
        ):
    return templates.TemplateResponse("back-db-main.html.j2", {
        "request": request
    })

@app.get("/messages/", response_model=MessageViewList)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            received_list: MessageList = Depends(get_received_list)
        ) -> MessageViewList:

    return MessageViewList(
        version=received_list.version,
        messages=list(received_list.get_after_version(last_version))
    )


@app.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            view_connections: WebSocketManager = Depends(get_view_connections)
        ):
    await view_connections.new_connection(websocket)
