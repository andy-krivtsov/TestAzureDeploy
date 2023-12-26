'''
Storage Worker demo application

Application runs in background, and processes requests over ServiceBus
'''
import logging
from asyncio import Task, create_task
from typing import Any

from fastapi import FastAPI

from demoapp.app.sp import ServiceProvider
from demoapp.app import AppBuilder
from demoapp.services import MessageList, AppSettings, MessagingService, WebSocketManager, StorageService
from demoapp.models import ComponentsEnum
from demoapp.controllers.back_storage import router, process_message
from demoapp.controllers.shared import ListUpdateHandler


#  Application initialization and FastAPI object
data_receiver_task: Task[Any] = None
list_update_handler: ListUpdateHandler = None

async def app_init(app: FastAPI, sp: ServiceProvider):
    global data_receiver_task, list_update_handler

    settings: AppSettings = sp.get_service(AppSettings)

    received_list = MessageList()
    con_manager = WebSocketManager()
    sp.register(MessageList, received_list)
    sp.register(WebSocketManager, con_manager)

    list_update_handler = ListUpdateHandler(con_manager)
    received_list.on_change_connect(list_update_handler.on_update)

    msg_srv: MessagingService = MessagingService(settings, app.state.component)
    sp.register(MessagingService, msg_srv)

    stor_srv = StorageService(settings)
    sp.register(StorageService, stor_srv)

    #data_receiver_task = create_task(msg_srv.receive_messages(process_message))

    data_receiver_task = create_task(
        msg_srv.receive_messages(
            processor=lambda msg: process_message(
                message=msg,
                received_list=received_list,
                stor_srv=stor_srv,
                msg_srv=msg_srv)
            )
        )

async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    global data_receiver_task

    msg_srv: MessagingService = sp.get_service(MessagingService)
    data_receiver_task.cancel()
    await msg_srv.close()

    stor_srv: StorageService = sp.get_service(StorageService)
    await stor_srv.close()

app = AppBuilder(ComponentsEnum.stor_service) \
        .with_static() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .build()

app.include_router(router)