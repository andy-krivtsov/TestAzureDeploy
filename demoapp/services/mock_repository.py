import random
import uuid
import logging
from typing import Any, Iterable
from datetime import datetime,timedelta, timezone
from demoapp.services.interface.repository import OrderRepository, ProcessingRepository, RepositoryAlreadyExistException, RepositoryNotFoundException
from demoapp.models import Order, OrderStatus, Customer, ProductItem, ProcessingItem, ProcessingStatus

class MemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: dict[str, Order] = {}
        self.generateTestOrders()

    async def create_order(self, order: Order):
        if order.id in self._orders:
            raise RepositoryAlreadyExistException(f"Order already exist: id == {order.id}")
        self._orders[order.id] = order

    async def get_order(self, id: str) -> Order:
        order = self._orders.get(id, None)
        if not order:
            raise RepositoryNotFoundException(f"Order not found: id={id}")
        return order

    async def get_orders(self, active: bool=False, limit: int=0, offset: int=0, sort: str="created", order: str="asc") -> Iterable[Order]:
        orders_list = sorted(
            filter(
                lambda x: self.filterActive(x, active),
                self._orders.values()
            ),
            key=lambda x: self.getSortKey(x, sort),
            reverse=(order =="desc")
        )

        if offset > len(orders_list) - 1:
            offset = len(orders_list) - 1

        if limit > 0:
            return orders_list[offset:offset + limit]
        else:
            return orders_list[offset:]

    async def get_orders_count(self) -> int:
        return len(self._orders)

    async def update_order(self, order: Order):
        if order.id not in self._orders:
            raise RepositoryNotFoundException(f"Order not exist: id == {order.id}")

        self._orders[order.id] = order

    async def delete_order(self, id: str):
        if id in self._orders:
            del(self._orders[id])

    async def delete_all_orders(self):
        self._orders.clear()

    async def close(self):
        pass

    def getSortKey(self, order: Order, field: str) -> Any:
        if field == 'id':
            return order.id
        elif field == 'created':
            return order.created
        elif field == 'customer':
            return order.customer.name
        elif field == 'due_date':
            return order.due_date
        elif field == 'status':
            return order.status
        else:
            return ""

    def filterActive(self, order: Order, active: bool) -> bool:
        # if not filtered return always True
        if not active:
            return True

        # if filtered created < 1h age or status != completed
        return ((order.status in [OrderStatus.new, OrderStatus.created] ) or
                (order.created > datetime.now(timezone.utc) - timedelta(minutes=15)))


    def generateTestOrders(self, n: int = 100):
        customers = [Customer(id=str(uuid.uuid4()), name=f"Customer Name #{i}") for i in range(20)]
        items = [ProductItem(id=str(uuid.uuid4()), name=f"Product Item #{i}") for i in range(20)]
        orders = [Order.get_random(customers, items) for i in range(n)]

        self._orders = { x.id: x for x in orders }



class MemoryProcessingRepository(ProcessingRepository):
    def __init__(self):
        self._items: dict[str, ProcessingItem] = {}

    async def create_item(self, item: ProcessingItem):
        if item.id in self._items:
            raise RepositoryAlreadyExistException(f"Item already exist: id == {item.id}")

        existed_item = await self.find_item_for_order(item.order.id)
        if existed_item:
            raise RepositoryAlreadyExistException(f"Item for order_id={item.order.id} already exist: id == {existed_item.id}")

        logging.info("Create item id=%s for order id=%s", item.id, item.order.id)
        self._items[item.id] = item

    async def find_item_for_order(self, order_id: str = None) -> ProcessingItem:
        found = [x for x in self._items.values() if x.order.id == order_id]
        return (found[0] if len(found) else None)

    async def get_item(self, id: str) -> ProcessingItem:
        item = self._items.get(id, None)
        if not item:
            raise RepositoryNotFoundException(f"Item not found: id={id}")
        return item

    async def get_items(self, status: ProcessingStatus = None) -> Iterable[ProcessingItem]:
        return sorted(
            filter(lambda x: self.filterItems(x, status), self._items.values()),
            key=lambda x: x.created,
            reverse=True
        )

    async def update_item(self, item: ProcessingItem):
        if item.id not in self._items:
            raise RepositoryNotFoundException(f"Item not exist: id == {item.id}")

        logging.info("Update item id=%s for order id=%s", item.id, item.order.id)

        self._items[item.id] = item


    async def delete_item(self, id: str):
        if id in self._items:
            del(self._items[id])

    async def delete_all_items(self):
        logging.warning("Delete all Processing Items")
        self._items.clear()

    async def close(self):
        pass

    def filterItems(self, item: ProcessingItem, status: ProcessingStatus = None):
        if item.created < datetime.now(timezone.utc) - timedelta(minutes=15):
            return False

        if status is not None:
            return item.status == status

        return True

