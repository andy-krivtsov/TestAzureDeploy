import uuid
from typing import Any, Iterable
from datetime import datetime,timedelta, timezone
from demoapp.services.order_repository import OrderRepository, OrderAlreadyExistException, OrderNotFoundException
from demoapp.models import Order, OrderStatus, Customer, ProductItem

class MemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: dict[str, Order] = {}
        self.generateTestOrders()

    async def create_order(self, order: Order):
        if order.id in self._orders:
            raise OrderAlreadyExistException(f"Order already exist: id == {order.id}")
        self._orders[order.id] = order

    async def get_order(self, id: str) -> Order:
        return self._orders.get(id, None)

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
            raise OrderNotFoundException(f"Order not exist: id == {order.id}")

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

