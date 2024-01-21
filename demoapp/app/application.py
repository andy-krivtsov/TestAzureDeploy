from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.trace import get_tracer_provider


from demoapp.app.logging import setup_logging
from demoapp.app.telemetry import SpanEnrichingProcessor
from demoapp.app.sp import ServiceProvider
from demoapp.models import ComponentsEnum
from demoapp.services import msal_auth_config, AppSettings
from demoapp.dep import app_settings


LIVENESS_PROBE_PATH = "/health/live"
READINESS_PROBE_PATH = "/health/ready"

async def simple_liveness(
            request: fastapi.Request,
            settings: AppSettings = fastapi.Depends(app_settings),
        ) -> Any:
    return {
        "status": "OK",
        "commit": settings.git_commit_sha
    }

class AppBuilder:
    class StaticMount(BaseModel):
        path: str
        file_path: Path
        name: str

    def __init__(self, component: ComponentsEnum):
        self._settings: AppSettings = None
        self._app_init: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable] = None
        self._app_shutdown: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable] = None

        self._component = component
        self._cors = True
        self._msal = True
        self._user_auth = False
        self._static: list[AppBuilder.StaticMount] = []
        self._healthprobes = True
        self._appinsights = True

    def with_settings(self, settings: AppSettings) -> AppBuilder:
        self._settings = settings
        return self

    def with_init(self, func: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
        self._app_init = func
        return self

    def with_shutdown(self, func: Callable[[fastapi.FastAPI, ServiceProvider], Awaitable]) -> AppBuilder:
        self._app_shutdown = func
        return self

    def with_cors(self, val: bool=True) -> AppBuilder:
        self._cors = val
        return self

    def with_msal(self, val: bool=True) -> AppBuilder:
        self._msal = val
        return self

    def with_user_auth(self, val: bool=True) -> AppBuilder:
        self._user_auth = val
        return self

    def with_static(self, path: str="/static", file_path: Path=Path("demoapp/static"), name: str="static") -> AppBuilder:
        self._static.append(AppBuilder.StaticMount(path=path, file_path=file_path, name=name))
        return self

    def with_healthprobes(self, val: bool=True) -> AppBuilder:
        self._healthprobes = val
        return self

    def with_appinsights(self, val: bool=True) -> AppBuilder:
        self._appinsights = val
        return self

    def build(self) -> fastapi.FastAPI:
        sp = ServiceProvider()

        if not self._settings:
            self._settings = AppSettings()

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
        app.state.sp = sp

        for mount in self._static:
            app.mount(path=mount.path, app=StaticFiles(directory=mount.file_path), name=mount.name)

        if self._healthprobes:
            app.add_api_route(LIVENESS_PROBE_PATH, endpoint=simple_liveness)

        if self._cors:
            app.add_middleware(
                CORSMiddleware, allow_origins=["*"],
                allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        if self._msal:
            msal_auth = MSALAuthorization(client_config=msal_auth_config(self._settings))
            sp.register(MSALAuthorization, msal_auth)

            app.add_middleware(SessionMiddleware, secret_key=self._settings.auth_session_key)

            if self._user_auth:
                app.include_router(msal_auth.router)

        return app

    @asynccontextmanager
    async def app_lifespan(self, app: fastapi.FastAPI):
        logging.info("Application lifecycle: initialization")
        sp: ServiceProvider = app.state.sp

        if self._app_init:
            await self._app_init(app, sp)

        yield
        logging.info("Application lifecycle: shutdown")

        if self._app_shutdown:
            await self._app_shutdown(app, sp)

