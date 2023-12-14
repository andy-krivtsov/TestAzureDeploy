from pydantic import Field
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    auth_client_id: str = Field(..., description="App Client ID")
    auth_client_secret: str = Field(..., description="App Client Secrets")
    auth_tenant_id: str = Field(..., description="App native tenant")
    auth_session_key: str = Field("", description="Session encryption key")

    auth_login_path: str = Field("/_login_route", description="MSAL login path in app")
    auth_token_path: str = Field("/token", description="MSAL token path in app")
    auth_logout_path: str = Field("/_logout_route", description="MSAL logout path in app")

    servicebus_namespace: str = Field(..., description="Service bus namespace name")
    servicebus_topic: str = Field(..., description="Service bus data topic name")
    servicebus_subscription: str = Field("", description="Service bus data topic subscription name")
    servicebus_status_queue: str = Field("", description="Service bus status queue name")
    servicebus_client_id: str = Field("demoapp", description="Service bus client identifier")

    db_url: str = Field("", description="CosmosDB url")
    db_database: str = Field("", description="CosmosDB database name")
    db_container: str = Field("", description="CosmosDB container name")

    storage_url: str = Field("", description="Storage account URL")
    storage_container: str = Field("", description="Storage account container")