'''
Frontend demo application

Application runs as user-facing WebApp
'''
from datetime import datetime, timezone
import logging
from typing import Annotated, cast

from fastapi import Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_msal import UserInfo

from demoapp.application import DemoApp
from demoapp.messages_lists import MessageList
from demoapp.settings import AppSettings
from demoapp.models import MessageDTO, ComponentsEnum, MessageStatusDTO, MessageStatusListDTO, StatusTagEnum
from demoapp.servicebus import QueueService
from demoapp.dependencies import app_settings, app_templates

class FrontApp(DemoApp):

    def __init__(self):
        super().__init__(component=ComponentsEnum.front_service)
        self.sent_list = MessageList()

    async def app_init(self):
        await super().app_init()
        self.setup_status_receiving()
        self.fastapi.mount("/static", StaticFiles(directory="demoapp/static"), name="static")

    async def process_status_message(self, message: MessageDTO):
        logging.info(f"Process status message: id={message.id}")

        self.sent_list.update_status(
            id=message.correlation_id,
            tag=StatusTagEnum.sent,
            value=True)


app = FrontApp()
def get_sent_list() -> MessageList:
    return app.sent_list

auth_scheme = app.optional_auth_scheme

# Path functions (API controllers)

@app.fastapi.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(app_settings),
        current_user: UserInfo = Depends(auth_scheme),
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
@app.fastapi.post("/messages/")
async def post_message(
        request: Request,
        message: MessageDTO,
        settings: AppSettings = Depends(app_settings),
        queue: QueueService = Depends(app.get_queue_service) ):

    logging.info(f"post_message(): Post message to the queue: {message.data}")

    await queue.send_message(message)

    app.sent_list.append(MessageStatusDTO(
        time=datetime.now(timezone.utc),
        message_id=message.id,
        data=str(message.data)
    ))
    return message

@app.fastapi.get("/messages/", response_model=MessageStatusListDTO)
async def get_messages(
            request: Request,
            last_version: Annotated[int, Query()] = -1,
            sent_list: MessageList = Depends(get_sent_list)
        ) -> MessageStatusListDTO:

    return MessageStatusListDTO(
        version=sent_list.version,
        messages=list(sent_list.get_after_version(last_version))
    )
