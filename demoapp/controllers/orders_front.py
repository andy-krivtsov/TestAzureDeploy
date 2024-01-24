import asyncio
import logging
import uuid
from typing import Annotated, Iterable, Union, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from fastapi_msal.models import UserInfo
from opentelemetry import baggage, trace, context
from http import HTTPStatus

from demoapp.app.sp import ServiceProvider
from demoapp import dep
from demoapp.services.metrics import created_messages_counter, processed_messages_counter
from demoapp.models import Customer, OrderStatus, ProcessingStatus, ProductItem, Order, PaginationOrdersList, OrderStatusUpdate, WebsocketConnectInfo
from demoapp.app import AppAttributes
from demoapp.services import AppSettings, OrderRepository, RepositoryAlreadyExistException, RepositoryNotFoundException, MessageService, WebsocketService


#===============================================================================
# Callback functions
#===============================================================================

STATUS_CONVERTING: dict[ProcessingStatus, OrderStatus] = {
    ProcessingStatus.processing: OrderStatus.processing,
    ProcessingStatus.completed: OrderStatus.completed,
    ProcessingStatus.error: OrderStatus.error
}

async def on_status_message(update: OrderStatusUpdate, sp: ServiceProvider):
    try:
        logging.info("Update order status: %s => %s", update.order_id, update.new_status)

        websocket_service: WebsocketService = sp.get_service(WebsocketService)
        order_repository: OrderRepository = sp.get_service(OrderRepository)

        order = await order_repository.get_order(update.order_id)

        order.status = STATUS_CONVERTING[update.new_status]
        await order_repository.update_order(order)

        await websocket_service.send_client_order_update([order])

    except RepositoryNotFoundException:
        logging.warning("Order not found: id=%s", update.order_id)

    except Exception:
        logging.exception("Error in status update processing!")

#===============================================================================
# Routing (HTTP path functions)
#===============================================================================

router = APIRouter()

# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(dep.app_settings),
        current_user: UserInfo = Depends(dep.optional_auth_scheme),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    return await get_page(
        request=request,
        page_name="new",
        settings=settings,
        current_user=current_user,
        templates=templates)

@router.get("/{page_name}", response_class=HTMLResponse)
async def get_page(
        request: Request,
        page_name: str = None,
        settings: AppSettings = Depends(dep.app_settings),
        current_user: UserInfo = Depends(dep.optional_auth_scheme),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    if current_user:
        username = current_user.display_name
    else:
        username = ""

    login_path = settings.auth_login_path
    if settings.auth_public_url:
        login_path = f"{settings.auth_login_path}?redirect_uri={settings.auth_public_url}{settings.auth_token_path}"

    try:
        return templates.TemplateResponse(f"pages/{page_name}.html.j2", {
            "request": request,
            "page_name": page_name,
            "settings": settings,
            "username": username,
            "login_path": login_path,
            "logout_path": settings.auth_logout_path
        })

    except TemplateNotFound:
        raise HTTPException(status_code=404, detail="Not found")

@router.get("/api/userinfo")
async def get_userinfo(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            current_user: UserInfo = Depends(dep.optional_auth_scheme)) -> UserInfo:
    return current_user if current_user else UserInfo()

@router.get("/api/websocketinfo")
async def get_websocket_info(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            websocket_service: WebsocketService = Depends(dep.websocket_service),
            current_user: UserInfo = Depends(dep.require_auth_scheme)) -> WebsocketConnectInfo:

    return await websocket_service.get_client_connection_info(current_user.user_id)


@router.get("/api/customers")
async def get_customers(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            current_user: UserInfo = Depends(dep.require_auth_scheme)) -> list[Customer]:
    return [
        Customer(id="0a3d007d-147d-45d5-bb68-43d55c23ebae", name="Customer Display Name #1"),
        Customer(id="9eeb9c60-e44a-4acb-9327-a662abcdc77c", name="Customer Display Name #2"),
        Customer(id="7d3efb20-1b65-41d1-b355-eb68f36bb940", name="Customer Display Name #3")
    ]

@router.get("/api/product-items")
async def get_product_items(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            current_user: UserInfo = Depends(dep.require_auth_scheme)) -> list[ProductItem]:
    return [
        ProductItem(id="4245a244-5bdf-4d04-be75-63ffbd902ba5", name="Product Item #1"),
        ProductItem(id="7701aee1-4ad1-47e1-ad49-ef968d40d731", name="Product Item #2"),
        ProductItem(id="4cc47581-0b75-4c35-8a83-33712f0991d3", name="Product Item #3")
    ]

@router.post("/api/orders", status_code=HTTPStatus.CREATED)
async def post_order(
            request: Request,
            order: Order,
            settings: AppSettings = Depends(dep.app_settings),
            repository: OrderRepository = Depends(dep.order_repository),
            message_service: MessageService = Depends(dep.message_service),
            websocket_service: WebsocketService = Depends(dep.websocket_service),
            current_user: UserInfo = Depends(dep.require_auth_scheme)) -> Order:

    try:
        logging.info("POST /api/orders: create new order: %s", order.model_dump_json(by_alias=True))

        order.status = OrderStatus.new
        await repository.create_order(order)

        asyncio.create_task(websocket_service.send_client_order_update([order]))

        await message_service.send_processing_message(order)

        return order
    except RepositoryAlreadyExistException as exc:
        logging.exception("Error in creating new order")
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=exc.args)

@router.get("/api/orders", response_model=Union[PaginationOrdersList, Iterable[Order]])
async def get_orders(
            request: Request,
            active: bool = False,
            offset: int = 0,
            limit: int = 0,
            sort: str = "created",
            order: str = "asc",
            settings: AppSettings = Depends(dep.app_settings),
            repository: OrderRepository = Depends(dep.order_repository),
            current_user: UserInfo = Depends(dep.require_auth_scheme)
    ) -> PaginationOrdersList | Iterable[Order]:

    data = await repository.get_orders(
        active=active,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order)

    if limit == 0:
        return data

    totalRows = await repository.get_orders_count()
    return PaginationOrdersList(
        total=totalRows,
        rows=data
    )

@router.delete("/api/orders")
async def delete_orders(
            request: Request,
            repository: OrderRepository = Depends(dep.order_repository),
            current_user: UserInfo = Depends(dep.require_auth_scheme)):
    try:
        logging.info("DELETE /api/orders: delete all orders")
        await repository.delete_all_orders()

    except Exception as exc:
        logging.exception("Error in deleting all orders")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=exc.args)

@router.post("/api/commands/generate-orders")
async def generate_test_orders(
            request: Request,
            repository: OrderRepository = Depends(dep.order_repository),
            current_user: UserInfo = Depends(dep.require_auth_scheme)):

    for order in get_test_orders():
        await repository.create_order(order)

def get_test_orders(n: int = 100) -> list[Order]:
    customers: list[Customer] = []
    items: list[ProductItem] = []
    orders: list[Order] = []

    customers = [Customer(id=str(uuid.uuid4()), name=f"Customer Name #{i}") for i in range(20)]
    items = [ProductItem(id=str(uuid.uuid4()), name=f"Product Item #{i}") for i in range(20)]

    orders = [Order.get_random(customers, items) for i in range(n)]
    return orders
