from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Type

import fastapi
#from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from opentelemetry.context.context import Context
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization
from uvicorn.logging import AccessFormatter, ColourizedFormatter
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.core.settings import settings
from opentelemetry.sdk.trace import Span, SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry import baggage
from opentelemetry.trace import get_tracer_provider


from demoapp.service_provider import ServiceProvider
from demoapp.models import ComponentsEnum
from demoapp.services.security import msal_auth_config
from demoapp.settings import AppSettings
from demoapp.services.dependencies import app_settings

settings.tracing_implementation = "opentelemetry"

LIVENESS_PROBE_PATH = "/health/live"
READINESS_PROBE_PATH = "/health/ready"

class AppAttributes:
    APP_MESSAGE_ID = "app.message_id"
    APP_STATUS_MESSAGE_ID = "app.status_message_id"
    APP_MESSAGE_DTO = "app.message_dto"
    APP_STATUS_VALUE = "app.status_value"

class SpanEnrichingProcessor(SpanProcessor):
    attrs_list: list[str] = [AppAttributes.APP_MESSAGE_ID, SpanAttributes.ENDUSER_ID]

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        super().on_start(span, parent_context)

        for k,v in baggage.get_all().items():
            if k in self.attrs_list:
                span.set_attribute(k, str(v))

async def simple_liveness(
            request: fastapi.Request,
            settings: AppSettings = fastapi.Depends(app_settings),
        ) -> Any:
    return {
        "status": "OK",
        "commit": settings.git_commit_sha
    }

class Application:
    class StaticMount(BaseModel):
        path: str
        file_path: Path
        name: str

    def __init__(
            self,
            component: ComponentsEnum,
            settings: AppSettings = AppSettings(),
            statics: list[StaticMount] = [StaticMount(path="/static", file_path=Path("demoapp/static"), name="static")],
            user_auth: bool = True,
            health_probes: bool = True,
            app_insights: bool = True,
            init_handler: Callable[[Application], Awaitable] = None,
            shutdown_handler: Callable[[Application], Awaitable] = None
        ):

        self._settings = settings
        self._init_handler = init_handler
        self._shutdown_handler = shutdown_handler

        setup_logging(settings)

        if app_insights:
            configure_azure_monitor(
                connection_string=self._settings.app_insights_constr,
                disable_offline_storage=True)
            get_tracer_provider().add_span_processor(SpanEnrichingProcessor())   # type: ignore

        self._component = component
        self._app = fastapi.FastAPI(lifespan=self.app_lifespan)
        self._app.state.component = self._component

        for mount in statics:
            self._app.mount(path=mount.path, app=StaticFiles(directory=mount.file_path), name=mount.name)

        if health_probes:
            self._app.add_api_route(path=LIVENESS_PROBE_PATH, endpoint=simple_liveness)

        self._app.add_middleware(
            CORSMiddleware, allow_origins=["*"],
            allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        self._msal_auth = MSALAuthorization(client_config=msal_auth_config(self._settings))

        if user_auth:
            self._app.add_middleware(SessionMiddleware, secret_key=self._settings.auth_session_key)
            self._app.include_router(self._msal_auth.router)

    @property
    def fastapi(self) -> fastapi.FastAPI:
        return self._app

    @property
    def auth(self) -> MSALAuthorization:
        return self._msal_auth

    @property
    def component(self) -> ComponentsEnum:
        return self._component

    @property
    def settings(self) -> AppSettings:
        return self._settings

    @asynccontextmanager
    async def app_lifespan(self, app: fastapi.FastAPI):
        await self.app_init(app)
        if self._init_handler:
            await self._init_handler(self)

        yield

        if self._shutdown_handler:
            await self._shutdown_handler(self)

        await self.app_shutdown(app)

    async def app_init(self, app: fastapi.FastAPI):
        pass

    async def app_shutdown(self, app: fastapi.FastAPI):
        pass

    @staticmethod
    def get_app() -> Application:
        global __GLOBAL_APPLICATION
        return __GLOBAL_APPLICATION


__GLOBAL_APPLICATION: Application = None

def get_application() -> Application:
    global __GLOBAL_APPLICATION
    return __GLOBAL_APPLICATION

def set_application(app: Application):
    global __GLOBAL_APPLICATION
    __GLOBAL_APPLICATION = app

#====================================================================================================================================
#====================================================================================================================================

class AppBuilder:
    class StaticMount(BaseModel):
        path: str
        file_path: Path
        name: str

    def __init__(self, component: ComponentsEnum):
        self._settings: AppSettings = None
        self._app_init: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable] = None
        self._app_shutdown: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable] = None

        self._cors = False
        self._msal = False
        self._user_auth = False
        self._component = component
        self._static: list[AppBuilder.StaticMount] = []
        self._liveness: str = None
        self._appinsights = False

    def with_settings(self, settings: AppSettings) -> AppBuilder:
        self._settings = settings
        return self

    def with_init(self, func: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
        self._app_init = func
        return self

    def with_shutdown(self, func: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
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

    def with_appinsights(self) -> AppBuilder:
        self._appinsights = True
        return self

    def build(self) -> fastapi.FastAPI:
        sp = ServiceProvider()

        if self._settings:
            sp.register(AppSettings, self._settings)
            setup_logging(self._settings)

        if self._appinsights:
            configure_azure_monitor(
                connection_string=self._settings.app_insights_constr,
                disable_offline_storage=True
            )
            get_tracer_provider().add_span_processor(SpanEnrichingProcessor())   # type: ignore

        app = fastapi.FastAPI(lifespan=self.app_lifespan)
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
    async def app_lifespan(self, app: fastapi.FastAPI):
        sp = ServiceProvider()

        # if self._settings:
        #     setup_logging(self._settings)

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
    #logger.handlers.clear()
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