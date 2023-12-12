import logging

from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy

class DbService:
    def __init__(
            self,
            url: str,
            credential: str | dict[str, str] | AsyncTokenCredential,
            database_name: str,
            container_name: str):
        self._client = CosmosClient(url=url, credential=credential)
        self.database_name = database_name
        self.container_name = container_name
        self._database: DatabaseProxy = None
        self._container: ContainerProxy = None

    async def close(self):
        await self._client.close()

    @property
    def client(self) -> CosmosClient:
        return self._client

    @property
    def database(self) -> DatabaseProxy:
        if not self._database:
            self._database = self._client.get_database_client(self.database_name)
        return self._database

    @property
    def container(self) -> ContainerProxy:
        if not self._container:
            self._container = self.database.get_container_client(self.container_name)
        return self._container
