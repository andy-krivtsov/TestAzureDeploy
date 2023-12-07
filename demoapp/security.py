import os
from fastapi import HTTPException, Request, status
from fastapi_msal import IDTokenClaims, MSALClientConfig
from fastapi_msal.security import MSALScheme
from fastapi.security.base import SecurityBase

def get_auth_config() -> MSALClientConfig:
    auth_config: MSALClientConfig = MSALClientConfig()
    auth_config.client_id = os.environ.get("AUTH_CLIENT_ID","democlient")
    auth_config.client_credential = os.environ.get("AUTH_CLIENT_SECRET","demosecret")
    auth_config.tenant =  os.environ.get("AUTH_TENANT","0000")
    return auth_config


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