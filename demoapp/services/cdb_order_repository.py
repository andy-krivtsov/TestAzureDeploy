import logging
from datetime import datetime,timedelta, timezone
from typing import Iterable

from azure.cosmos.aio import CosmosClient
from fastapi.encoders import jsonable_encoder

from demoapp.services.base_repository import OrderRepository
from demoapp.models import Order
from demoapp.services.cdb_exceptions import convert_cosmosdb_exceptions

class CosmosDBOrderRepository(OrderRepository):
    def __init__(self, cosmos_client: CosmosClient, db_name: str, container_name: str):
        self._container_name = container_name

        self._client = cosmos_client
        self._database = cosmos_client.get_database_client(db_name)
        self._container = self._database.get_container_client(container_name)

    async def close(self):
        pass

    @convert_cosmosdb_exceptions
    async def create_order(self, order: Order):
        logging.info("Create order in DB: %s", order.model_dump_json(by_alias=True))

        await self._container.create_item(jsonable_encoder(order))

    @convert_cosmosdb_exceptions
    async def get_order(self, id: str) -> Order:
        logging.info("Get order from DB: id=%s", id)

        item = await self._container.read_item(item=id, partition_key=id)
        return Order.model_validate(item)

    def build_query_order_by(self, sort: str, order: str) -> str:
        prop_name = ""

        if sort in ['id', 'created', 'status']:
            prop_name = sort
        elif sort == 'customer':
            prop_name = "customer.name"
        elif sort == 'due_date':
            prop_name = "dueDate"
        else:
            raise ValueError(f"Invalid sort field: {sort}")

        if order not in ['asc', 'desc']:
            raise ValueError(f"Invalid order: {order}")

        return f"ORDER BY c.{prop_name} {order.upper()}"


    def build_get_query(self, active: bool, limit: int, offset: int, sort: str, order: str) -> str:
        if limit < 0 or offset < 0:
            raise ValueError("Incorrect OFFSET or LIMIT")

        query = [ f'SELECT * FROM {self._container_name} c' ]

        limit_date = datetime.now(timezone.utc) - timedelta(minutes=120)
        limit_timestamp = int(round(limit_date.timestamp() * 1000))

        if active:
            query.append(f'WHERE DateTimeToTimestamp(c.created) > {limit_timestamp}')
            query.append('ORDER BY c.created DESC')
        else:
            query.append(self.build_query_order_by(sort, order))

        if limit > 0:
            query.append(f"OFFSET {offset} LIMIT {limit}")

        return " ".join(query)

    @convert_cosmosdb_exceptions
    async def get_orders(self, active: bool=False, limit: int=0, offset: int=0, sort: str="created", order: str="asc") -> Iterable[Order]:
        query=self.build_get_query(active, limit, offset, sort, order)

        logging.info("Get orders from DB: active=%s, query='%s'", active, query)

        items = self._container.query_items(query)
        return [Order.model_validate(x) async for x in items]

    @convert_cosmosdb_exceptions
    async def get_orders_count(self) -> int:
        query = f"SELECT VALUE COUNT(1) FROM {self._container_name} c"

        logging.info("Get number of documents, query = %s", query)

        ret = [ x async for x in self._container.query_items(query=query) ]
        return int(ret[0])          # type: ignore

    @convert_cosmosdb_exceptions
    async def update_order(self, order: Order):
        logging.info("Update order in DB: id=%s", order.id)
        await self._container.replace_item(item = order.id, body=jsonable_encoder(order))

    @convert_cosmosdb_exceptions
    async def delete_order(self, id: str):
        logging.info("Delete order from DB: id=%s", id)
        await self._container.delete_item(item=id, partition_key=id)

    @convert_cosmosdb_exceptions
    async def delete_all_orders(self):
        logging.warning("Delete all orders from DB")
        query = f"SELECT VALUE {{ id: c.id }} FROM {self._container_name} c"

        logging.info("  Select query: %s", query)
        items = self._container.query_items(query=query)

        async for item in items:
            id = item["id"]
            logging.info("  Deleting item: id=%s", id)
            await self._container.delete_item(item=id, partition_key=id)
