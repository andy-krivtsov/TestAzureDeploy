'''
Frontend demo application

Application runs as user-facing WebApp
'''
import logging
from asyncio import Task, create_task
from typing import Annotated, Any

from fastapi import FastAPI, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_msal import UserInfo

from demoapp.application import AppBuilder, ServiceProvider
from demoapp.messages_lists import MessageList
from demoapp.settings import AppSettings
from demoapp.models import MessageDTO, StatusData, ComponentsEnum, MessageStatusDTO, MessageStatusListDTO, StatusTagEnum
from demoapp.servicebus import QueueService
from demoapp.dependencies import app_settings, app_templates, global_service, optional_auth_scheme

status_receiver_task: Task[Any] = None

sent_list = MessageList()
def get_sent_list() -> MessageList:
    return sent_list

async def process_status_message(message: MessageDTO):
    try:
        status_data: StatusData = message.data
        logging.info(f"Process: {message.model_dump_json()}")

        get_sent_list().update_status(
            id=message.correlation_id,
            tag=status_data.tag,
            value=status_data.value)
    except Exception as exc:
        logging.error(f"Exception in status message processing: {exc}")

async def app_init(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task
    settings: AppSettings = sp.get_service(AppSettings)

    queue: QueueService = QueueService(settings, app.state.component)
    sp.register(QueueService, queue)

    status_receiver_task = create_task(queue.receive_messages(process_status_message,True))


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
        message: MessageDTO,
        settings: AppSettings = Depends(app_settings),
        queue: QueueService = Depends(global_service(QueueService)),
        sent_list: MessageList = Depends(get_sent_list)
    ):
    logging.info(f"post_message(): Post message to the queue: {message.data}")

    await queue.send_message(message)
    dto = MessageStatusDTO.fromMessage(message)
    dto.set_status(StatusTagEnum.sent, True)
    sent_list.append(dto)

    return message

@app.get("/messages/", response_model=MessageStatusListDTO)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            sent_list: MessageList = Depends(get_sent_list)
        ) -> MessageStatusListDTO:

    return MessageStatusListDTO(
        version=sent_list.version,
        messages=list(sent_list.get_after_version(last_version))
    )
