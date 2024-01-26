from typing import Any, Type

from fastapi import Depends
from fastapi.requests import HTTPConnection
from fastapi.templating import Jinja2Templates
from fastapi_msal import MSALAuthorization, IDTokenClaims

from demoapp.app.sp import ServiceProvider
from demoapp.services import (AppSettings, MSALOptionalScheme, OrderRepository, ProcessingRepository,
                              MessageService, WebsocketService)

from demoapp.services.azure_websocket import AzureWebsocketService

def get_global_service(req: HTTPConnection, T: Type) -> Any:
    sp: ServiceProvider = req.app.state.sp
    return sp.get_service(T)

def app_templates(req: HTTPConnection) -> Jinja2Templates:
    return get_global_service(req, Jinja2Templates)

def app_settings(req: HTTPConnection) -> AppSettings:
    return get_global_service(req, AppSettings)

def auth_service(req: HTTPConnection) -> MSALAuthorization:
    return get_global_service(req, MSALAuthorization)

async def require_auth_scheme(req: HTTPConnection, msal_auth: MSALAuthorization=Depends(auth_service)) -> IDTokenClaims:
    return await MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=True)(req)

async def optional_auth_scheme(req: HTTPConnection, msal_auth: MSALAuthorization=Depends(auth_service)) -> IDTokenClaims:
    return await MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)(req)

def order_repository(req: HTTPConnection) -> OrderRepository:
    return get_global_service(req, OrderRepository)

def processing_repository(req: HTTPConnection) -> ProcessingRepository:
    return get_global_service(req, ProcessingRepository)

def message_service(req: HTTPConnection) -> MessageService:
    return get_global_service(req, MessageService)

def websocket_service(req: HTTPConnection) -> WebsocketService:
    return get_global_service(req, WebsocketService)

def azure_websocket_service(req: HTTPConnection) -> AzureWebsocketService:
    return get_global_service(req, AzureWebsocketService)