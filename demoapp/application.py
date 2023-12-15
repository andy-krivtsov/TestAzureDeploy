from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable, Type

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization
from uvicorn.logging import AccessFormatter, ColourizedFormatter

from demoapp.models import ComponentsEnum
from demoapp.services.security import msal_auth_config
from demoapp.settings import AppSettings

LIVENESS_PROBE_PATH = "/health/live"
READINESS_PROBE_PATH = "/health/ready"

class ServiceProvider(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ServiceProvider, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, "services"):
            self.services: dict[Type, Any] = {}

    def register(self, service_type: Type, service: Any):
        self.services[service_type] = service

    def get_service(self, service_type: Type) -> Any:
        return self.services.get(service_type, None)

async def simple_liveness(request: Request) -> Any:
    return {"status": "OK"}

class AppBuilder:
    class StaticMount(BaseModel):
        path: str
        file_path: Path
        name: str

    def __init__(self, component: ComponentsEnum):
        self._settings: AppSettings = None
        self._app_init: Callable[[FastAPI, ServiceProvider], Awaitable] = None
        self._app_shutdown: Callable[[FastAPI, ServiceProvider], Awaitable] = None

        self._cors = False
        self._msal = False
        self._user_auth = False
        self._component = component
        self._static: list[AppBuilder.StaticMount] = []
        self._liveness: str = None

    def with_settings(self, settings: AppSettings) -> AppBuilder:
        self._settings = settings
        return self

    def with_init(self, func: Callable[[FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
        self._app_init = func
        return self

    def with_shutdown(self, func: Callable[[FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
        self._app_shutdown = func
        return self

    def with_cors(self) -> AppBuilder:
        self._cors = True
        return self

    def with_msal(self) -> AppBuilder:
        self._msal = True
        return self

    def with_user_auth(self) -> AppBuilder:
        self._user_auth = True
        return self

    def with_static(self, path: str="/static", file_path: Path=Path("demoapp/static"), name: str="static") -> AppBuilder:
        self._static.append(AppBuilder.StaticMount(path=path, file_path=file_path, name=name))
        return self

    def with_liveness(self, path=LIVENESS_PROBE_PATH) -> AppBuilder:
        self._liveness = path
        return self

    def build(self) -> FastAPI:
        sp = ServiceProvider()

        if self._settings:
            sp.register(AppSettings, self._settings)

        app = FastAPI(lifespan=self.app_lifespan)
        app.state.component = self._component

        for mount in self._static:
            app.mount(path=mount.path, app=StaticFiles(directory=mount.file_path), name=mount.name)

        if self._liveness:
            app.add_api_route(path=self._liveness, endpoint=simple_liveness)

        if self._cors:
            app.add_middleware(
                CORSMiddleware, allow_origins=["*"],
                allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        if self._settings:
            if self._msal:
                msal_auth = MSALAuthorization(client_config=msal_auth_config(self._settings))
                sp.register(MSALAuthorization, msal_auth)

                if self._user_auth:
                    app.add_middleware(SessionMiddleware, secret_key=self._settings.auth_session_key)
                    app.include_router(msal_auth.router)

        return app

    @asynccontextmanager
    async def app_lifespan(self, app: FastAPI):
        sp = ServiceProvider()

        if self._settings:
            setup_logging(self._settings)

        if self._app_init:
            await self._app_init(app, sp)

        yield

        if self._app_shutdown:
            await self._app_shutdown(app, sp)


class EndpointLoggingFilter(logging.Filter):
    def __init__(self, paths: list[str]):
        self.paths = paths

    def filter(self, record: logging.LogRecord) -> bool:
        for p in self.paths:
            if record.getMessage().find(p) != -1:
                return False
        return True


def setup_logging(settings: AppSettings) -> None:
    # Root logger
    logger = logging.getLogger()
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    color_formatter = ColourizedFormatter(
        fmt="{asctime} {levelprefix}{module}: {message}",
        style="{")

    handler.setFormatter(color_formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Uvicorn loggers
    uvicorn_root = logging.getLogger("uvicorn")
    uvicorn_root.handlers[0].setFormatter(color_formatter)

    acc_logger = logging.getLogger("uvicorn.access")
    acc_logger.handlers[0].setFormatter(AccessFormatter(
        fmt="{asctime} {levelprefix}{message}",
        style="{"
    ))
    acc_logger.addFilter(EndpointLoggingFilter([LIVENESS_PROBE_PATH]))

    # Azure SDK loggers
    azure_logger = logging.getLogger("azure")
    azure_logger.setLevel(logging.WARNING)