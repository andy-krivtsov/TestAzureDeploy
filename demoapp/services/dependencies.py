from typing import Any, Type
from pathlib import Path
from fastapi.templating import Jinja2Templates
from demoapp.application import ServiceProvider
from demoapp.services.security import MSALOptionalScheme
from fastapi_msal import MSALAuthorization

from demoapp.settings import AppSettings


def global_service(service_type: Type) -> Any:
    return lambda: ServiceProvider().get_service(service_type)

def require_auth_scheme() -> MSALOptionalScheme:
    msal_auth: MSALAuthorization = global_service(MSALAuthorization)()
    return MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=True)

def optional_auth_scheme() -> MSALOptionalScheme:
    msal_auth: MSALAuthorization = global_service(MSALAuthorization)()
    return MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)

def app_settings() -> AppSettings:
    return global_service(AppSettings)()

def app_templates() -> Jinja2Templates:
    tpl_path = Path(__file__).absolute().parent.joinpath("../templates")
    return Jinja2Templates(directory=tpl_path)

