import logging
from typing import Annotated
import uuid
import asyncio
import json

from http import HTTPStatus
from fastapi import Body, FastAPI, APIRouter, Request, Response, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from cloudevents.http import from_http

from azure.identity.aio import ClientSecretCredential
from azure.messaging.webpubsubservice.aio import WebPubSubServiceClient   # type: ignore
from pydantic import AnyUrl

from demoapp.services.interface.websocket import WebsocketService
from demoapp.models import Order, ProcessingItem, WebsocketConnectInfo
from demoapp.services.settings import AppSettings

router = APIRouter()

@router.options("/notifications/events")
async def options_events(
            request: Request,
            response: Response,
            webhook_request_origin: Annotated[str | None, Header()] = None):

    logging.info("Web PubSub validation: WebHook-Request-Origin: %s", webhook_request_origin)

    if not webhook_request_origin.endswith("webpubsub.azure.com"):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=f"Incorrect WebHook-Request-Origin: {webhook_request_origin}")

    return Response(status_code=204, headers= {
        "Allow": "OPTIONS, POST",
        "WebHook-Allowed-Origin": "*",
        "WebHook-Allowed-Rate": "100"
    })

@router.post("/notifications/events")
async def post_events(
            request: Request,
            response: Response):

    data = await request.body()
    event = from_http(headers=request.headers, data=data)  # type: ignore

    userId = event.get("userId", "")
    match event["type"]:
        case "azure.webpubsub.sys.connect":
            logging.info("Web PubSub connect request: userId: %s, connectionId: %s, hub: %s",
                         userId, event["connectionid"], event["hub"])

        case "azure.webpubsub.sys.connected":
            logging.info("Web PubSub user is connected: userId: %s, connectionId: %s, hub: %s",
                         userId, event["connectionid"], event["hub"])

        case "azure.webpubsub.sys.disconnected":
            logging.info("Web PubSub user is disconnected: userId: %s, connectionId: %s, hub: %s",
                         userId, event["connectionid"], event["hub"])

        case _:
            data = event.data
            logging.info("Web PubSub user/custom event: userId: %s, type: %s, content-type: %s, data: %s",
                         userId, event["type"], event["datacontenttype"], data)

    response.status_code = HTTPStatus.NO_CONTENT

class AzureWebsocketService(WebsocketService):

    def __init__(self, app: FastAPI, settings: AppSettings, credential: ClientSecretCredential):
        super().__init__(app, settings)
        app.include_router(router)

        self._client = WebPubSubServiceClient(
            endpoint=settings.web_pubsub_endpoint,
            hub=settings.web_pubsub_hub,
            credential=credential
        )

    async def close(self):
        await self._client.close()

    async def get_client_connection_info(self, user_id: str) -> WebsocketConnectInfo:
        token_data = await self._client.get_client_access_token(user_id=user_id, roles=[], minutes_to_expire=180)

        return WebsocketConnectInfo(
            url=AnyUrl(token_data['url']),
            protocol="json.webpubsub.azure.v1"
        )

    async def send_client_order_update(self, orders: list[Order]):
        try:
            logging.info("Send orders to Web PubSub clients")

            data = [jsonable_encoder(x) for x in orders]

            await self._client.send_to_all(
                message=data,
                content_type="application/json"
            )
        except Exception as exc:
            logging.exception("Error in sending to web pubsub")

    async def send_client_processing_update(self, items: list[ProcessingItem]):
        pass
