import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization, MSALClientConfig
from demoapp.models import ComponentsEnum, MessageDTO

from demoapp.security import MSALOptionalScheme
from demoapp.settings import AppSettings
from demoapp.servicebus import QueueService
from demoapp.logging import setup_logging
from demoapp.dependencies import app_settings

class DemoApp:
    def __init__(
            self,
            component: ComponentsEnum,
            user_auth: bool = True,
            settings: AppSettings = app_settings()):
        self.component = component
        self.settings = settings

        self._fastapi = FastAPI(lifespan=self.app_lifespan)

        self._fastapi.add_middleware(CORSMiddleware, allow_origins=["*"],
                                 allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        self.msal_auth = MSALAuthorization(client_config=msal_auth_config(settings))

        if user_auth:
            self._fastapi.add_middleware(SessionMiddleware, secret_key=settings.auth_session_key)
            self._fastapi.include_router(self.msal_auth.router)

        self.queue_service = QueueService(self.settings, self.component)
        self.data_receiver_task = None
        self.status_receiver_task = None

    @property
    def fastapi(self) -> FastAPI:
        return self._fastapi

    @property
    def optional_auth_scheme(self) -> MSALOptionalScheme:
        return MSALOptionalScheme(scheme=self.msal_auth.scheme, auth_required=False)

    @asynccontextmanager
    async def app_lifespan(self, app: FastAPI):
        await self.app_init()
        yield
        await self.app_shutdown()

    async def app_init(self):
        logging.info("Application initialization!")
        setup_logging(app_settings())

    async def app_shutdown(self):
        logging.info("Application shutdown!")

        if self.data_receiver_task:
            self.data_receiver_task.cancel()

        if self.status_receiver_task:
            self.status_receiver_task.cancel()

        await self.queue_service.close()

    def setup_data_receiving(self):
        self.data_receiver_task = asyncio.create_task(
            self.queue_service.receive_messages(self.process_message))

    def setup_status_receiving(self):
        self.status_receiver_task = asyncio.create_task(
            self.queue_service.receive_messages(self.process_status_message, True))

    async def process_message(self, message: MessageDTO):
        logging.info(f"Process message: id={message.id}")

    async def process_status_message(self, message: MessageDTO):
        logging.info(f"Process status message: id={message.id}")

    def get_queue_service(self) -> QueueService:
        return self.queue_service


def msal_auth_config(settings: AppSettings) -> MSALClientConfig:
    auth_config: MSALClientConfig = MSALClientConfig()
    auth_config.client_id = settings.auth_client_id
    auth_config.client_credential = settings.auth_client_secret
    auth_config.tenant = settings.auth_tenant_id

    auth_config.login_path = settings.auth_login_path
    auth_config.token_path = settings.auth_token_path
    auth_config.logout_path = settings.auth_logout_path

    return auth_config
