'''
Test demo application

Application runs as user-facing WebApp
'''
import asyncio
import logging
from asyncio import Task, create_task
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from azure.identity.aio import ClientSecretCredential
from azure.cosmos.aio import CosmosClient
from fastapi.templating import Jinja2Templates

from demoapp.app.sp import ServiceProvider
from demoapp.app import AppBuilder
from demoapp.models import ComponentsEnum
from demoapp.controllers.orders_back import router, on_processing_message
from demoapp.services import (AppSettings, ProcessingRepository, CosmosDBProcessingRepository,
                              MessageService, MockFrontService, ServiceBusMessageService, WebsocketService, LocalWebsocketService)

processing_task: asyncio.Task = None

async def app_init(app: FastAPI, sp: ServiceProvider):
    global processing_task

    logging.info("Back application initialization: create services")

    tpl_path = Path(__file__).absolute().parent.joinpath("templates/back")
    sp.register(Jinja2Templates, Jinja2Templates(directory=tpl_path))

    settings: AppSettings = sp.get_service(AppSettings)

    azure_cret = ClientSecretCredential(
        tenant_id=settings.auth_tenant_id,
        client_id=settings.auth_client_id,
        client_secret=settings.auth_client_secret)

    cosmos_client = CosmosClient(url=settings.db_url, credential=azure_cret)  # type: ignore

    sp.register(ClientSecretCredential, azure_cret)
    sp.register(CosmosClient, cosmos_client)

    repository = CosmosDBProcessingRepository(
        cosmos_client=cosmos_client,
        db_name=settings.db_database,
        container_name=settings.db_container
    )
    sp.register(ProcessingRepository, repository)

    websocket_service = LocalWebsocketService(app, settings)
    sp.register(WebsocketService, websocket_service)

    message_service = ServiceBusMessageService(sp)
    message_service.subscribe_processing_messages(on_processing_message)
    sp.register(MessageService, message_service)

async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    message_service: MessageService = sp.get_service(MessageService)
    await message_service.close()

    azure_cret: ClientSecretCredential = sp.get_service(ClientSecretCredential)
    cosmos_client: CosmosClient = sp.get_service(CosmosClient)

    await cosmos_client.close()
    await azure_cret.close()

app = AppBuilder(ComponentsEnum.back_service) \
        .with_static() \
        .with_appinsights() \
        .with_healthprobes() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .build()

app.include_router(router)

