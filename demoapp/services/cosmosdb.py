from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import uuid

from azure.identity.aio import ClientSecretCredential
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy

from demoapp.services import AppSettings
from demoapp.models import Message

class DatabaseService:
    def __init__(self, settings: AppSettings, sessionId: str = str(uuid.uuid4())):
        self.settings = settings
        self.sessionId = sessionId

        self._credential = ClientSecretCredential(
            tenant_id=settings.auth_tenant_id,
            client_id=settings.auth_client_id,
            client_secret=settings.auth_client_secret)

        self._client = CosmosClient(url=settings.db_url, credential=self._credential)  # type: ignore

        self._database: DatabaseProxy = None
        self._container: ContainerProxy = None

    async def close(self):
        if self._credential:
            await self._credential.close()
        if self._client:
            await self._client.close()

    @property
    def client(self) -> CosmosClient:
        return self._client

    @property
    def database(self) -> DatabaseProxy:
        if not self._database:
            self._database = self._client.get_database_client(self.settings.db_database)
        return self._database

    @property
    def container(self) -> ContainerProxy:
        if not self._container:
            self._container = self.database.get_container_client(self.settings.db_container)
        return self._container

    async def write_message(self, message: Message):
        logging.info(f"Write message to DB: {message.model_dump_json(by_alias=True)}, sessionId: {self.sessionId}")

        msg = message.model_dump()
        ret = await self.container.create_item({
            'id': msg['id'],
            'sessionId': self.sessionId,
            'time': datetime.now(timezone.utc).isoformat(),
            'data': msg['data']
        })

        logging.info(f"DB Write result: {json.dumps(ret)}")
