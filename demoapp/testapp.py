'''
Test application
'''

import logging
from fastapi import Depends, FastAPI, Request
from fastapi_msal import UserInfo

from demoapp.models import ComponentsEnum
from demoapp.application import AppBuilder, ServiceProvider
from demoapp.dependencies import app_settings, AppSettings
from demoapp.servicebus import QueueService
from demoapp.depend import global_service, optional_auth_scheme


class DemoService:
    def __init__(self, data):
        self._data = data

    @property
    def data(self) -> str:
        return self._data

class DemoService2:
    def __init__(self, data):
        self._data = data

    @property
    def data(self) -> str:
        return self._data

async def app_init(app: FastAPI, sp: ServiceProvider, settings: AppSettings = app_settings()):
    logging.info("Demo app init!")

    sp.register(QueueService, QueueService(settings, app.state.component))

    sp.register(DemoService, DemoService(settings.auth_tenant_id))
    sp.register(DemoService2, DemoService2(settings.auth_client_id))

app = AppBuilder(ComponentsEnum.front_service)\
        .with_settings(app_settings()) \
        .with_cors() \
        .with_msal() \
        .with_user_auth() \
        .with_init(app_init) \
        .build()

@app.get("/")
async def get_root(
            request: Request,
            srv: DemoService = Depends(global_service(DemoService)),
            srv2: DemoService2 = Depends(global_service(DemoService2)),
            current_user: UserInfo = Depends(optional_auth_scheme),
            queue_service: QueueService = Depends(global_service(QueueService))
        ):
    return {
        "title": "Test FastAPI application!",
        "service_data": srv.data,
        "service2_data": srv2.data
    }

