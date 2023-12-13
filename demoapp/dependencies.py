from pathlib import Path

from fastapi.templating import Jinja2Templates

from demoapp.settings import AppSettings

from typing import Any, Type
from demoapp.application import ServiceProvider
from demoapp.security import MSALOptionalScheme
from fastapi_msal import MSALAuthorization

def global_service(service_type: Type) -> Any:
    return lambda: ServiceProvider().get_service(service_type)

def optional_auth_scheme() -> MSALOptionalScheme:
    msal_auth: MSALAuthorization = global_service(MSALAuthorization)()
    return MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)

def app_settings() -> AppSettings:
    return global_service(AppSettings)()

def app_templates() -> Jinja2Templates:
    tpl_path = Path(__file__).absolute().parent.joinpath("templates")
    return Jinja2Templates(directory=tpl_path)

