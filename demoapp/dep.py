from pathlib import Path
from typing import Any, Type

from fastapi import Depends
from fastapi.requests import HTTPConnection
from fastapi.templating import Jinja2Templates
from fastapi_msal import MSALAuthorization, IDTokenClaims

from demoapp.app.sp import ServiceProvider
from demoapp.services import AppSettings, MessageList, MSALOptionalScheme, MessagingService, WebSocketManager

def get_global_service(req: HTTPConnection, T: Type) -> Any:
    sp: ServiceProvider = req.app.state.sp
    return sp.get_service(T)

def app_templates() -> Jinja2Templates:
    tpl_path = Path(__file__).absolute().parent.joinpath("templates")
    return Jinja2Templates(directory=tpl_path)

def app_settings(req: HTTPConnection) -> AppSettings:
    return get_global_service(req, AppSettings)

def auth_service(req: HTTPConnection) -> MSALAuthorization:
    return get_global_service(req, MSALAuthorization)

async def require_auth_scheme(req: HTTPConnection, msal_auth: MSALAuthorization=Depends(auth_service)) -> IDTokenClaims:
    return await MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=True)(req)

async def optional_auth_scheme(req: HTTPConnection, msal_auth: MSALAuthorization=Depends(auth_service)) -> IDTokenClaims:
    return await MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)(req)

def message_list(req: HTTPConnection) -> MessageList:
    return get_global_service(req, MessageList)

def messaging_service(req: HTTPConnection) -> MessagingService:
    return get_global_service(req, MessagingService)

def websocket_manager(req: HTTPConnection) -> WebSocketManager:
    return get_global_service(req, WebSocketManager)

