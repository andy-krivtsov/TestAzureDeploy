import asyncio
import logging
import uuid
import random
from typing import Iterable
from datetime import datetime,timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from opentelemetry import baggage, trace, context
from http import HTTPStatus

from demoapp.app.sp import ServiceProvider
from demoapp import dep
from demoapp.services.metrics import created_messages_counter, processed_messages_counter
from demoapp.models import Customer, Order, ProcessingItem, ProcessingStatus, ProductItem, WebsocketConnectInfo
from demoapp.services import AppSettings, ProcessingRepository, WebsocketService, OrderProcessor


#===============================================================================
# Callback functions
#===============================================================================

async def on_processing_message(order: Order, sp: ServiceProvider):
    new_item = ProcessingItem(
        id=str(uuid.uuid4()),
        order=order,
        created=datetime.now(timezone.utc),
        processing_time=random.randint(10, 30),
        status=ProcessingStatus.new
    )

    logging.info("Start order processing, id: %s, time: %s seconds", order.id, new_item.processing_time)

    processor = OrderProcessor(new_item, sp)
    await processor.create_item()
    asyncio.create_task(processor.process())


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

    return await repository.get_items(time_period=timedelta(minutes=120))

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
            id=id,
            created=order.created + timedelta(seconds=5),
            started=order.created + timedelta(seconds=6),
            order=order,
            processing_time=random.randint(5, 180),
            finished=finished,
            status=status
        ))

    return items
