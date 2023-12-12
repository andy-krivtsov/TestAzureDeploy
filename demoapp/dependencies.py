from pathlib import Path

from azure.identity.aio import ClientSecretCredential
from fastapi import Depends
from fastapi.templating import Jinja2Templates

from demoapp.settings import AppSettings
from demoapp.database import DbService

_settings: AppSettings = None
_db_service: DbService = None

def app_settings() -> AppSettings:
    global _settings

    if not _settings:
        _settings = AppSettings()
    return _settings

def db_service(settings: AppSettings = Depends(app_settings)) -> DbService:
    global _db_service

    if not _db_service:
        credential = ClientSecretCredential(
            tenant_id=settings.auth_tenant_id,
            client_id=settings.auth_client_id,
            client_secret=settings.auth_client_secret
        )

        _db_service = DbService(
            url=settings.db_url,
            database_name=settings.db_database,
            container_name=settings.db_container,
            credential=credential)

    return _db_service

def app_templates() -> Jinja2Templates:
    tpl_path = Path(__file__).absolute().parent.joinpath("templates")
    return Jinja2Templates(directory=tpl_path)

