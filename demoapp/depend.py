from typing import Any, Type
from demoapp.application import ServiceProvider
from demoapp.security import MSALOptionalScheme
from fastapi_msal import MSALAuthorization

def global_service(service_type: Type) -> Any:
    return lambda: ServiceProvider().get_service(service_type)

def optional_auth_scheme() -> MSALOptionalScheme:
    msal_auth: MSALAuthorization = global_service(MSALAuthorization)()
    return MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)
