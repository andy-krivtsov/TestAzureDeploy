from fastapi import HTTPException, Request, status
from fastapi_msal import IDTokenClaims, MSALClientConfig
from fastapi_msal.security import MSALScheme
from fastapi.security.base import SecurityBase

from demoapp.settings import AppSettings

class MSALOptionalScheme(SecurityBase):
    def __init__(self, scheme: MSALScheme, auth_required: bool=True):
        self.scheme = scheme
        self.auth_required = auth_required

    async def __call__(self, request: Request) -> IDTokenClaims:
        try:
            return await self.scheme(request)
        except HTTPException as exc:
            if (exc.status_code == status.HTTP_401_UNAUTHORIZED) and not self.auth_required:
                return None
            raise exc

def msal_auth_config(settings: AppSettings) -> MSALClientConfig:
    auth_config: MSALClientConfig = MSALClientConfig()
    auth_config.client_id = settings.auth_client_id
    auth_config.client_credential = settings.auth_client_secret
    auth_config.tenant = settings.auth_tenant_id

    auth_config.login_path = settings.auth_login_path
    auth_config.token_path = settings.auth_token_path
    auth_config.logout_path = settings.auth_logout_path

    return auth_config
