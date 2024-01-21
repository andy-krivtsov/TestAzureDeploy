import asyncio
import logging
import uuid
import random
from typing import Annotated, Iterable, Union, cast
from datetime import datetime,timedelta, timezone

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
from demoapp.models import Customer, Order, ProcessingItem, OrderStatus, OrderStatusUpdate, ProcessingStatus, ProductItem, WebsocketConnectInfo
from demoapp.app import AppAttributes
from demoapp.services import AppSettings, ProcessingRepository, RepositoryAlreadyExistException, RepositoryNotFoundException, MessageService, WebsocketService


#===============================================================================
# Callback functions
#===============================================================================

async def send_status_update(item: ProcessingItem, sp: ServiceProvider):
    message_service: MessageService = sp.get_service(MessageService)
    websocket_service: WebsocketService = sp.get_service(WebsocketService)

    await message_service.send_status_message(OrderStatusUpdate(
        order_id=item.order.id,
        new_status=item.status
    ))

    await websocket_service.send_client_processing_update([ item ])


async def on_processing_message(order: Order, sp: ServiceProvider):
    try:
        repository: ProcessingRepository = sp.get_service(ProcessingRepository)

        processing_time = random.randint(10, 30)
        new_item = ProcessingItem(
            id=str(uuid.uuid4()),
            order=order,
            created=datetime.now(timezone.utc),
            processing_time=processing_time,
            status=ProcessingStatus.processing
        )
        await repository.create_item(new_item)

        logging.info("Start order processing, id: %s, time: %s seconds", order.id, processing_time)
        await send_status_update(new_item, sp)

    except Exception:
        logging.exception("Error in status update processing!")


async def background_order_processing(sp: ServiceProvider):
    try:
        repository: ProcessingRepository = sp.get_service(ProcessingRepository)

        while True:
            logging.info("Background orders processing")

            d = datetime.now(timezone.utc)

            for item in await repository.get_items(ProcessingStatus.processing):
                if d >= item.created + timedelta(seconds=item.processing_time):
                    logging.info("Order processing is finished, id = %s, order = %s", item.id, item.order.id)
                    item.finished = d
                    item.status = ProcessingStatus.completed
                    await repository.update_item(item)

                    await send_status_update(item, sp)

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logging.info("Orders processing background task is canceled!")


#===============================================================================
# Routing (HTTP path functions)
#===============================================================================

router = APIRouter()

# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(dep.app_settings),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    return await get_page(
        request=request,
        page_name="processing",
        settings=settings,
        templates=templates)

@router.get("/{page_name}", response_class=HTMLResponse)
async def get_page(
        request: Request,
        page_name: str = None,
        settings: AppSettings = Depends(dep.app_settings),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    try:
        return templates.TemplateResponse(f"pages/{page_name}.html.j2", {
            "request": request,
            "page_name": page_name,
            "settings": settings
        })

    except TemplateNotFound:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/api/processing", response_model=Iterable[ProcessingItem])
async def get_processing_items(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            repository: ProcessingRepository = Depends(dep.processing_repository)
    ) -> Iterable[ProcessingItem]:

    return await repository.get_items()

@router.delete("/api/processing")
async def delete_processing_items(
            request: Request,
            repository: ProcessingRepository = Depends(dep.processing_repository)):
    try:
        logging.info("DELETE /api/processing: delete all processing items")
        await repository.delete_all_items()

    except Exception as exc:
        logging.exception("Error in deleting all items")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=exc.args)

@router.get("/api/websocketinfo")
async def get_websocket_info(
            request: Request,
            settings: AppSettings = Depends(dep.app_settings),
            websocket_service: WebsocketService = Depends(dep.websocket_service)
        ) -> WebsocketConnectInfo:

    return await websocket_service.get_client_connection_info("")



@router.post("/api/commands/generate-items")
async def generate_test_items(
            request: Request,
            repository: ProcessingRepository = Depends(dep.processing_repository)):

    for item in get_test_items(n=30):
        await repository.create_item(item)

def get_test_items(n: int = 100) -> list[ProcessingItem]:
    customers = [Customer(id=str(uuid.uuid4()), name=f"Customer Name #{i}") for i in range(20)]
    prodItems = [ProductItem(id=str(uuid.uuid4()), name=f"Product Item #{i}") for i in range(20)]
    orders = [Order.get_random(customers, prodItems, datetime.now(timezone.utc) - timedelta(seconds=random.randint(30, 600))) for i in range(n)]

    items: list[ProcessingItem] = []
    for order in orders:
        processing_time = random.randint(5, 180)
        id = str(uuid.uuid4())

        status = random.choice(list(ProcessingStatus))
        if status in [ProcessingStatus.completed, ProcessingStatus.error]:
            finished = order.created + timedelta(seconds=5) + timedelta(seconds=processing_time)
        else:
            finished = None

        items.append(ProcessingItem(
            id = id,
            created = order.created + timedelta(seconds=5),
            order=order,
            processing_time=random.randint(5, 180),
            finished=finished,
            status=status
        ))

    return items
