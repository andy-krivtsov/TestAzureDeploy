import logging
from typing import Annotated, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_msal.models import UserInfo
from opentelemetry import baggage, trace, context

from demoapp import dep
from demoapp.services.metrics import created_messages_counter, processed_messages_counter
from demoapp.models import Message, MessageViewDTO, MessageViewList, StatusMessage, StatusTagEnum
from demoapp.app import AppAttributes
from demoapp.services import AppSettings, MessagingService, MessageList, WebSocketManager

tracer = trace.get_tracer(__name__)

#===============================================================================
# Processing functions
#===============================================================================

# New message processing (from frontend via websocket)
async def new_message(message: Message, msg_srv: MessagingService, sent_list: MessageList):
    ctx = baggage.set_baggage(AppAttributes.APP_MESSAGE_ID, message.id)
    ctx_token = context.attach(ctx)
    try:
        with tracer.start_as_current_span(
                name="Front: New Message",
                kind=trace.SpanKind.SERVER,
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
async def process_status_message(status_message: Message, sent_list: MessageList):
    try:
        with tracer.start_as_current_span(
                name="Front: new status message processing",
                kind=trace.SpanKind.SERVER,
                attributes={AppAttributes.APP_STATUS_MESSAGE_ID: status_message.id}):
            status_msg = cast(StatusMessage, status_message)
            logging.info(f"Process status message: {status_msg.model_dump_json()}")

            await sent_list.update_status(
                id=status_message.correlation_id,
                tag=status_msg.data.tag,
                value=status_msg.data.value)

            message = sent_list.get_by_id(status_message.correlation_id)
            if message and message.is_completed():
                processed_messages_counter.add(1)

    except Exception as exc:
        logging.exception("Exception %s in status message processing, id=%s, message: %s", type(exc), status_message.id, exc )

#===============================================================================
# Routing (HTTP path functions)
#===============================================================================

router = APIRouter()

# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(dep.app_settings),
        current_user: UserInfo = Depends(dep.optional_auth_scheme),
        templates: Jinja2Templates = Depends(dep.app_templates)):

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
@router.post("/messages/")
async def post_message(
        request: Request,
        message: Message,
        msg_srv: MessagingService = Depends(dep.messaging_service),
        current_user: UserInfo = Depends(dep.require_auth_scheme),
        sent_list: MessageList = Depends(dep.message_list)
    ):
    if not current_user:
        raise HTTPException(status_code=401, detail="User is unauthorized")

    logging.info(f"post_message(): new message: {message.id}")
    return await new_message(message=message, msg_srv=msg_srv, sent_list=sent_list)

@router.get("/messages/", response_model=MessageViewList)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            current_user: UserInfo = Depends(dep.require_auth_scheme),
            sent_list: MessageList = Depends(dep.message_list)
        ) -> MessageViewList:

    if not current_user:
        raise HTTPException(status_code=401, detail="User is unauthorized")

    return MessageViewList(
        version=sent_list.version,
        messages=list(sent_list.get_after_version(last_version))
    )

@router.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            current_user: UserInfo = Depends(dep.require_auth_scheme),
            con_manager: WebSocketManager = Depends(dep.websocket_manager),
            sent_list: MessageList = Depends(dep.message_list),
            msg_rv: MessagingService = Depends(dep.messaging_service),
        ):
    # Create new connection and send initial state (current list)
    id = await con_manager.add_connection(websocket, current_user)
    logging.info("WebSocket: new connection from user = %s, id = %s",
                 current_user.display_name if current_user else None, id)

    logging.info("WebSocket: sent complete list to the new connection")
    await con_manager.send_messages(sent_list.messages, id)

    # Start received messages processing
    await con_manager.start_receiving(
        id=id,
        on_received=lambda data: new_message(
            message=Message.model_validate(data),
            msg_srv=msg_rv,
            sent_list=sent_list))
