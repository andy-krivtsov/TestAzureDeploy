import logging
from datetime import datetime,timedelta, timezone
from typing import Iterable

from azure.cosmos.aio import CosmosClient
from fastapi.encoders import jsonable_encoder

from demoapp.services.base_repository import ProcessingRepository
from demoapp.models import ProcessingItem, ProcessingStatus
from demoapp.services.cdb_exceptions import convert_cosmosdb_exceptions

class CosmosDBProcessingRepository(ProcessingRepository):
    def __init__(self, cosmos_client: CosmosClient, db_name: str, container_name: str):
        self._container_name = container_name

        self._client = cosmos_client
        self._database = cosmos_client.get_database_client(db_name)
        self._container = self._database.get_container_client(container_name)

    async def close(self):
        pass

    @convert_cosmosdb_exceptions
    async def create_item(self, item: ProcessingItem):
        logging.info("Create processing item: %s", item.model_dump_json(by_alias=True))
        await self._container.create_item(jsonable_encoder(item))

    @convert_cosmosdb_exceptions
    async def get_item(self, id: str) -> ProcessingItem:
        logging.info("Get processing item: id=%s", id)

        item = await self._container.read_item(item=id, partition_key=id)
        return ProcessingItem.model_validate(item)

    @convert_cosmosdb_exceptions
    async def find_item_for_order(self, order_id: str = None) -> ProcessingItem:
        query = f'SELECT * FROM {self._container_name} c WHERE c.order.id = @order_id'
        params = [{ 'name': "@order_id", 'value': order_id }]
        logging.info("Get processing item for order: order_id: %s, query: %s", order_id, query)

        items = [x async for x in self._container.query_items(query=query, parameters=params)]

        if not items:
            return None

        return ProcessingItem.model_validate(items[0])

    def build_get_query(self, status: ProcessingStatus) -> tuple[str, list]:
        query = [ f'SELECT * FROM {self._container_name} c' ]

        limit_date = datetime.now(timezone.utc) - timedelta(minutes=15)
        limit_timestamp = int(round(limit_date.timestamp() * 1000))

        where = [ "DateTimeToTimestamp(c.created) > @timestamp" ]
        params = [{ "name": "@timestamp", "value": limit_timestamp }]

        if status is not None:
            where.append("c.status = @status")
            params.append({ "name": "@status", "value": str(status) })

        query.append("WHERE " + "AND".join(where))
        query.append("ORDER BY c.created DESC")

        return " ".join(query), params

    @convert_cosmosdb_exceptions
    async def get_items(self, status: ProcessingStatus = None) -> Iterable[ProcessingItem]:
        query, params = self.build_get_query(status)
        logging.info("Get processing items: query: %s",  query)

        items = self._container.query_items(query=query, parameters=params)
        return [ProcessingItem.model_validate(x) async for x in items]

    @convert_cosmosdb_exceptions
    async def update_item(self, item: ProcessingItem):
        logging.info("Update processing item: id=%s", item.id)
        await self._container.replace_item(item = item.id, body=jsonable_encoder(item))

    @convert_cosmosdb_exceptions
    async def delete_item(self, id: str):
        logging.info("Delete processing item: id=%s", id)
        await self._container.delete_item(item=id, partition_key=id)


    @convert_cosmosdb_exceptions
    async def delete_all_items(self):
        logging.warning("Delete all processing items")
        query = f"SELECT VALUE {{ id: c.id }} FROM {self._container_name} c"

        logging.info("  Select query: %s", query)
        items = self._container.query_items(query=query)

        async for item in items:
            id = item["id"]
            logging.info("  Deleting item: id=%s", id)
            await self._container.delete_item(item=id, partition_key=id)

