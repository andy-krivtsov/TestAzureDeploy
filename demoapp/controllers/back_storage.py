import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from opentelemetry import trace

from demoapp import dep
from demoapp.services.metrics import processed_messages_counter
from demoapp.models import Message, MessageViewDTO, MessageViewList, StatusTagEnum
from demoapp.services import MessagingService, MessageList, WebSocketManager, StorageService

tracer = trace.get_tracer(__name__)

#===============================================================================
# Processing functions
#===============================================================================

# Incoming Service Bus  messages processing
async def process_message(
        message: Message,
        received_list: MessageList,
        stor_srv: StorageService,
        msg_srv: MessagingService
    ):
    try:
        with tracer.start_as_current_span(
                name="BackStorage: Incoming new message",
                kind=trace.SpanKind.SERVER):

            logging.info("Process data message: id=%s", message.id)

            dto = MessageViewDTO.fromMessage(message, {StatusTagEnum.received: True})
            await received_list.append(dto)

            await stor_srv.save_message(message)

            await msg_srv.send_status_message(
                tag=StatusTagEnum.storage,
                value=True,
                correlation_id=message.id)

        await received_list.update_status(message.id, StatusTagEnum.storage, True)

        processed_messages_counter.add(1)
    except Exception:
        logging.exception("Exception in message processing! id=%s", message.id)


#===============================================================================
# Routing (HTTP path functions)
#===============================================================================

router = APIRouter()

# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
async def get_root(
            request: Request,
            templates: Jinja2Templates = Depends(dep.app_templates)
        ):

    return templates.TemplateResponse("back-stor-main.html.j2", {
        "request": request
    })

@router.get("/messages/", response_model=MessageViewList)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            received_list: MessageList = Depends(dep.message_list)
        ) -> MessageViewList:

    return MessageViewList(
        version=received_list.version,
        messages=list(received_list.get_after_version(last_version))
    )


@router.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            con_manager: WebSocketManager = Depends(dep.websocket_manager),
            received_list: MessageList = Depends(dep.message_list)
        ):
    # Create new connection and send initial state (current list)
    id = await con_manager.add_connection(websocket)
    logging.info("WebSocket: new connection id = %s", id)

    logging.info("WebSocket: sent complete list to the new connection")
    await con_manager.send_messages(received_list.messages, id)

    # Start receiving loop (without processing input)
    await con_manager.start_receiving(id)
