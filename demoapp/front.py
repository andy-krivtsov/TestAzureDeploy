'''
Frontend demo application

Application runs as user-facing WebApp
'''
import logging
from asyncio import Task, create_task
from typing import Annotated, Any, cast

from fastapi import FastAPI, HTTPException, Query, Request, Depends, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_msal import UserInfo
from opentelemetry.trace import get_tracer, SpanKind
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry import baggage
from opentelemetry import context

from demoapp.service_provider import ServiceProvider
from demoapp.application import AppBuilder, AppAttributes
from demoapp.services.messagelist import MessageList
from demoapp.settings import AppSettings
from demoapp.models import Message, ComponentsEnum, MessageViewDTO, MessageViewList, StatusMessage, StatusTagEnum
from demoapp.services.servicebus import MessagingService
from demoapp.services.dependencies import app_settings, app_templates, global_service, optional_auth_scheme, require_auth_scheme
from demoapp.services.websocket import WebSocketManager
from demoapp.services.metrics import created_messages_counter, processed_messages_counter

tracer = get_tracer(__name__)

# Sent message list
sent_list = MessageList()
def get_sent_list() -> MessageList:
    return sent_list

# WebSocket management and event handlers
async def new_connect_handler(connection: WebSocket, current_user: UserInfo = None):
    logging.info("WebSocket: connection from user = %s", current_user.display_name if current_user else None)
    logging.info("WebSocket: sent complete list to the new connection")
    await WebSocketManager.send_json(
        connection,
        [ x.model_dump() for x in sent_list.messages ]
    )

view_connections = WebSocketManager(
    on_connection=new_connect_handler,
    on_received=lambda data: new_message(
        message=Message.model_validate(data),
        msg_srv=global_service(MessagingService)(),
        sent_list=sent_list)
)

def get_view_connections() -> WebSocketManager:
    return view_connections

# Sent list update event handler (sent event to websocket)
async def sent_list_update_handler(sender: Any, message_info: MessageViewDTO, **kwargs):
    await view_connections.send_message(message_info)

sent_list.on_change_connect(sent_list_update_handler)

# New message processing
async def new_message(message: Message, msg_srv: MessagingService, sent_list: MessageList):
    ctx = baggage.set_baggage(AppAttributes.APP_MESSAGE_ID, message.id)
    ctx_token = context.attach(ctx)
    try:
        with tracer.start_as_current_span(
                name="Front: New Message",
                kind=SpanKind.SERVER,
                attributes={AppAttributes.APP_MESSAGE_ID: message.id}):

                logging.info(f"Put new message to the queue: {message.id}")

                await msg_srv.send_message(message)
                dto = MessageViewDTO.fromMessage(message, {StatusTagEnum.sent: True})
                await sent_list.append(dto)

                created_messages_counter.add(1)
    finally:
        context.detach(ctx_token)

    return message


# Incoming Service Bus status messages processing
async def process_status_message(status_message: Message):
    try:
        with tracer.start_as_current_span(
                name="Front: new status message processing",
                kind=SpanKind.SERVER,
                attributes={AppAttributes.APP_STATUS_MESSAGE_ID: status_message.id}):
            status_msg = cast(StatusMessage, status_message)
            logging.info(f"Process status message: {status_msg.model_dump_json()}")

            sent_list = get_sent_list()
            await sent_list.update_status(
                id=status_message.correlation_id,
                tag=status_msg.data.tag,
                value=status_msg.data.value)

            message = sent_list.get_by_id(status_message.correlation_id)
            if message.is_completed():
                processed_messages_counter.add(1)

    except Exception as exc:
        logging.exception("Exception %s in status message processing, id=%s, message: %s", type(exc), status_message.id, exc )

#  Application initialization and FastAPI object
status_receiver_task: Task[Any] = None
async def app_init(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task
    settings: AppSettings = sp.get_service(AppSettings)

    msg_srv: MessagingService = MessagingService(settings, app.state.component)
    sp.register(MessagingService, msg_srv)

    status_receiver_task = create_task(msg_srv.receive_messages(process_status_message,True))

async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task

    msg_srv: MessagingService = sp.get_service(MessagingService)
    status_receiver_task.cancel()
    await msg_srv.close()

app = AppBuilder(ComponentsEnum.front_service)\
        .with_settings(AppSettings()) \
        .with_cors() \
        .with_static() \
        .with_liveness() \
        .with_msal() \
        .with_user_auth() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .with_appinsights() \
        .build()

require_scheme = require_auth_scheme()
optional_scheme = optional_auth_scheme()

# Path functions (API controllers)
@app.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(app_settings),
        current_user: UserInfo = Depends(optional_scheme),
        templates: Jinja2Templates = Depends(app_templates)):

    if current_user:
        username = current_user.preferred_username
    else:
        username = ""

    login_path = settings.auth_login_path
    if settings.auth_public_url:
        login_path = f"{settings.auth_login_path}?redirect_uri={settings.auth_public_url}{settings.auth_token_path}"

    return templates.TemplateResponse("front-main.html.j2", {
        "request": request,
        "settings": settings,
        "username": username,
        "login_path": login_path,
        "logout_path": settings.auth_logout_path,
    })

# post message to the data topic
@app.post("/messages/")
async def post_message(
        request: Request,
        message: Message,
        msg_srv: MessagingService = Depends(global_service(MessagingService)),
        current_user: UserInfo = Depends(require_scheme),
        sent_list: MessageList = Depends(get_sent_list)
    ):
    if not current_user:
        raise HTTPException(status_code=401, detail="User is unauthorized")

    logging.info(f"post_message(): new message: {message.id}")
    return await new_message(message=message, msg_srv=msg_srv, sent_list=sent_list)

@app.get("/messages/", response_model=MessageViewList)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            current_user: UserInfo = Depends(require_scheme),
            sent_list: MessageList = Depends(get_sent_list)
        ) -> MessageViewList:

    if not current_user:
        raise HTTPException(status_code=401, detail="User is unauthorized")

    return MessageViewList(
        version=sent_list.version,
        messages=list(sent_list.get_after_version(last_version))
    )

@app.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            current_user: UserInfo = Depends(require_scheme),
            view_connections: WebSocketManager = Depends(get_view_connections)
        ):
    await view_connections.new_connection(websocket, current_user)
