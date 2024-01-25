'''
Test demo application

Application runs as user-facing WebApp
'''
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
from demoapp.controllers.orders_front import router, on_status_message
from demoapp.services import (AppSettings, OrderRepository, CosmosDBOrderRepository,
                              MessageService, ServiceBusMessageService, MockProcessingService,
                              WebsocketService, LocalWebsocketService, AzureWebsocketService)


async def app_init(app: FastAPI, sp: ServiceProvider):
    logging.info("Front application initialization: create services")

    tpl_path = Path(__file__).absolute().parent.joinpath("templates/front")
    sp.register(Jinja2Templates, Jinja2Templates(directory=tpl_path))

    settings: AppSettings = sp.get_service(AppSettings)

    azure_cred = ClientSecretCredential(
        tenant_id=settings.auth_tenant_id,
        client_id=settings.auth_client_id,
        client_secret=settings.auth_client_secret)

    cosmos_client = CosmosClient(url=settings.db_url, credential=azure_cred)  # type: ignore

    sp.register(ClientSecretCredential, azure_cred)
    sp.register(CosmosClient, cosmos_client)

    repository = CosmosDBOrderRepository(
        cosmos_client=cosmos_client,
        db_name=settings.db_database,
        container_name=settings.db_container
    )
    sp.register(OrderRepository, repository)

#    websocket_service = LocalWebsocketService(app, settings)
#    sp.register(WebsocketService, websocket_service)

    websocket_service = AzureWebsocketService(app, settings, azure_cred)
    sp.register(WebsocketService, websocket_service)

    #message_service = MockMessageService(sp)
    message_service = ServiceBusMessageService(sp)
    message_service.subscribe_status_messages(on_status_message)
    sp.register(MessageService, message_service)

    # mock_processor = MockProcessingService(message_service)
    # sp.register(MockProcessingService, mock_processor)


async def app_shutdown(app: FastAPI, sp: ServiceProvider):
    message_service: MessageService = sp.get_service(MessageService)
    await message_service.close()

    websocket_service = sp.get_service(WebsocketService)
    await websocket_service.close()

#    websocket_service2 = sp.get_service(AzureWebsocketService)
#    await websocket_service2.close()

    azure_cred: ClientSecretCredential = sp.get_service(ClientSecretCredential)
    cosmos_client: CosmosClient = sp.get_service(CosmosClient)

    await cosmos_client.close()
    await azure_cred.close()


app = AppBuilder(ComponentsEnum.front_service) \
        .with_static() \
        .with_user_auth() \
        .with_appinsights() \
        .with_healthprobes() \
        .with_init(app_init) \
        .with_shutdown(app_shutdown) \
        .build()

app.include_router(router)

