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

    auth_public_url: str = Field("", description="Public-facing application URL (redirect URL for OpenID)")

    servicebus_namespace: str = Field(..., description="Service bus namespace name")
    servicebus_orders_topic: str = Field(..., description="Service bus orders topic name")
    servicebus_status_topic: str = Field(..., description="Service bus status topic name")
    servicebus_orders_sub: str = Field("", description="Service bus orders topic subscription name")
    servicebus_status_sub: str = Field("", description="Service bus status topic subscription name")
    servicebus_client_id: str = Field("demoapp", description="Service bus client identifier")

    db_url: str = Field("", description="CosmosDB url")
    db_database: str = Field("", description="CosmosDB database name")
    db_container: str = Field("", description="CosmosDB container name")

    storage_url: str = Field("", description="Storage account URL")
    storage_container: str = Field("", description="Storage account container")

    app_insights_constr: str = Field("", description="App Insights connection string")

    web_pubsub_endpoint: str = Field("", description="Web PubSub service endpoint")
    web_pubsub_hub: str = Field("", description="Web PubSub service Hub name")

    git_commit_sha: str = Field("", description="Git commit of this build")

    otel_service_name: str = Field("", description="Open Telemetry service name")