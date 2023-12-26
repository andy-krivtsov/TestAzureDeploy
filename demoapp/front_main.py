'''
Frontend demo application

Application runs as user-facing WebApp
'''
import logging
from asyncio import Task, create_task
from typing import Any

from fastapi import FastAPI

from demoapp.app.sp import ServiceProvider
from demoapp.app import AppBuilder
from demoapp.services import MessageList, AppSettings, MessagingService, WebSocketManager
from demoapp.models import ComponentsEnum
from demoapp.controllers.front import router, process_status_message
from demoapp.controllers.shared import ListUpdateHandler

#  Application initialization and FastAPI object
status_receiver_task: Task[Any] = None
list_update_handler: ListUpdateHandler = None

async def app_init(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task, list_update_handler

    settings: AppSettings = sp.get_service(AppSettings)

    sent_list = MessageList()
    con_manager = WebSocketManager()
    sp.register(MessageList, sent_list)
    sp.register(WebSocketManager, con_manager)

    list_update_handler = ListUpdateHandler(con_manager)
    sent_list.on_change_connect(list_update_handler.on_update)

    msg_srv: MessagingService = MessagingService(settings, app.state.component)
    sp.register(MessagingService, msg_srv)

    status_receiver_task = create_task(
        msg_srv.receive_messages(
            status=True,
            processor=lambda msg: process_status_message(status_message=msg, sent_list=sent_list))
        )

async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    global status_receiver_task

    msg_srv: MessagingService = sp.get_service(MessagingService)
    status_receiver_task.cancel()
    await msg_srv.close()

app = AppBuilder(ComponentsEnum.front_service) \
        .with_static() \
        .with_user_auth() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .build()

app.include_router(router)
