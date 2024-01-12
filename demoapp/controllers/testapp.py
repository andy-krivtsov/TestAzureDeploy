import logging
from typing import Annotated, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from fastapi_msal.models import UserInfo
from opentelemetry import baggage, trace, context

from demoapp import dep
from demoapp.services.metrics import created_messages_counter, processed_messages_counter
from demoapp.models import Message, MessageViewDTO, MessageViewList, StatusMessage, StatusTagEnum
from demoapp.app import AppAttributes
from demoapp.services import AppSettings, MessagingService, MessageList, WebSocketManager


router = APIRouter()


# Path functions (API controllers)
@router.get("/", response_class=HTMLResponse)
async def get_root(
        request: Request,
        settings: AppSettings = Depends(dep.app_settings),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    return await get_page(
        request=request,
        page_name="new",
        settings=settings,
        templates=templates)

@router.get("/{page_name}", response_class=HTMLResponse)
async def get_page(
        request: Request,
        page_name: str = None,
        settings: AppSettings = Depends(dep.app_settings),
        templates: Jinja2Templates = Depends(dep.app_templates)):

    username = "Demo User"

    try:
        return templates.TemplateResponse(f"pages/{page_name}.html.j2", {
            "request": request,
            "page_name": page_name,
            "settings": settings,
            "username": username
        })

    except TemplateNotFound:
        raise HTTPException(status_code=404, detail="Not found")