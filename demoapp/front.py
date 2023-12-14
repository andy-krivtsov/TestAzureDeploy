'''
Frontend demo application

Application runs as user-facing WebApp
'''
import logging
from asyncio import Task, create_task
from typing import Annotated, Any, cast

from fastapi import FastAPI, Query, Request, Depends, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_msal import UserInfo

from demoapp.application import AppBuilder, ServiceProvider
from demoapp.services.messagelist import MessageList
from demoapp.settings import AppSettings
from demoapp.models import Message, ComponentsEnum, MessageViewDTO, MessageViewList, StatusMessage, StatusTagEnum
from demoapp.services.servicebus import MessagingService
from demoapp.services.dependencies import app_settings, app_templates, global_service, optional_auth_scheme
from demoapp.services.websocket import WebSocketManager

# Sent message list
sent_list = MessageList()
def get_sent_list() -> MessageList:
    return sent_list

# WebSocket management and event handlers
async def new_connect_handler(connection: WebSocket):
    logging.info("WebSocket: sent complete list to the new connection")
    await WebSocketManager.send_json(
        connection,
        [ x.model_dump() for x in sent_list.messages ]
    )

view_connections = WebSocketManager(on_connection=new_connect_handler)
def get_view_connections() -> WebSocketManager:
    return view_connections

# Sent list update event handler (sent event to websocket)
async def sent_list_update_handler(sender: Any, message_info: MessageViewDTO, **kwargs):
    await view_connections.send_message(message_info)

sent_list.on_change_connect(sent_list_update_handler)


# Incoming Service Bus status messages processing
async def process_status_message(message: Message):
    try:
        status_msg = cast(StatusMessage, message)
        logging.info(f"Process status message: {status_msg.model_dump_json()}")

        await get_sent_list().update_status(
            id=message.correlation_id,
            tag=status_msg.data.tag,
            value=status_msg.data.value)

    except Exception as exc:
        logging.exception("Exception %s in status message processing, id=%s, message: %s", type(exc), message.id, exc )

#  Application initialization and FastAPI object
status_receiver_task: Task[Any] = None
async def app_init(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task
    settings: AppSettings = sp.get_service(AppSettings)

    msg_srv: MessagingService = MessagingService(settings, app.state.component)
    sp.register(MessagingService, msg_srv)

    status_receiver_task = create_task(msg_srv.receive_messages(process_status_message,True))


app = AppBuilder(ComponentsEnum.front_service)\
        .with_settings(AppSettings()) \
        .with_cors() \
        .with_static() \
        .with_msal() \
        .with_user_auth() \
        .with_init(app_init) \
        .build()

scheme = optional_auth_scheme

# Path functions (API controllers)
@app.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(app_settings),
        current_user: UserInfo = Depends(optional_auth_scheme()),
        templates: Jinja2Templates = Depends(app_templates)):

    if current_user:
        username = current_user.preferred_username
    else:
        username = None

    return templates.TemplateResponse("front-main.html.j2", {
        "request": request,
        "settings": settings,
        "username": username,
        "login_path": settings.auth_login_path,
        "logout_path": settings.auth_logout_path,
    })

# post message to the data topic
@app.post("/messages/")
async def post_message(
        request: Request,
        message: Message,
        msg_srv: MessagingService = Depends(global_service(MessagingService)),
        sent_list: MessageList = Depends(get_sent_list)
    ):
    logging.info(f"post_message(): Post message to the queue: {message.data}")

    await msg_srv.send_message(message)
    dto = MessageViewDTO.fromMessage(message)
    dto.set_status(StatusTagEnum.sent, True)
    await sent_list.append(dto)

    return message

@app.get("/messages/", response_model=MessageViewList)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            sent_list: MessageList = Depends(get_sent_list)
        ) -> MessageViewList:

    return MessageViewList(
        version=sent_list.version,
        messages=list(sent_list.get_after_version(last_version))
    )

@app.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            view_connections: WebSocketManager = Depends(get_view_connections)
        ):
    await view_connections.new_connection(websocket)