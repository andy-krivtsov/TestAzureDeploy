import logging
from typing import cast
from fastapi import APIRouter
from opentelemetry import context, trace, baggage

from demoapp.app import FrontApp, AppAttributes
from demoapp.models import Message, StatusMessage

tracer = trace.get_tracer(__name__)

router = APIRouter()

# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
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
@router.post("/messages/")
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

@router.get("/messages/", response_model=MessageViewList)
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

@router.websocket("/view/feed")
async def view_websocket(
            websocket: WebSocket,
            current_user: UserInfo = Depends(require_scheme),
            view_connections: WebSocketManager = Depends(get_view_connections)
        ):
    await view_connections.new_connection(websocket, current_user)



# Incoming Service Bus status messages processing
async def process_status_message(status_message: Message, app: FrontApp):
    try:
        with tracer.start_as_current_span(
                name="Front: new status message processing",
                kind=trace.SpanKind.SERVER,
                attributes={AppAttributes.APP_STATUS_MESSAGE_ID: status_message.id}):
            status_msg = cast(StatusMessage, status_message)
            logging.info(f"Process status message: {status_msg.model_dump_json()}")

            await app.sent_list.update_status(
                id=status_message.correlation_id,
                tag=status_msg.data.tag,
                value=status_msg.data.value)

            message = app.sent_list.get_by_id(status_message.correlation_id)
            # if message.is_completed():
            #     processed_messages_counter.add(1)

    except Exception as exc:
        logging.exception("Exception %s in status message processing, id=%s, message: %s", type(exc), status_message.id, exc )
