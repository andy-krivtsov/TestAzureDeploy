import json
import logging
from typing import Any, Awaitable, Callable, Mapping
import uuid
import asyncio

from azure.identity.aio import ClientSecretCredential
from azure.servicebus.aio import ServiceBusClient, ServiceBusSender, ServiceBusReceiver
from azure.servicebus import ServiceBusReceiveMode, ServiceBusReceivedMessage, ServiceBusMessage
from azure.servicebus.exceptions import MessageLockLostError, SessionLockLostError, MessageAlreadySettled
from pydantic import BaseModel
from opentelemetry import context, propagate


from demoapp.models import ComponentsEnum, Message, MessageStatusData, StatusMessage, StatusTagEnum
from demoapp.services import AppSettings

class MessagingService:

    def __init__(self, settings: AppSettings, component: ComponentsEnum):
        self.settings = settings
        self.component = component

        self._credential = ClientSecretCredential(
            tenant_id=settings.auth_tenant_id,
            client_id=settings.auth_client_id,
            client_secret=settings.auth_client_secret)

        self._client = ServiceBusClient(settings.servicebus_namespace, self._credential)

        self._sender: ServiceBusSender = None
        self._status_sender: ServiceBusSender = None
        self._receiver: ServiceBusReceiver = None
        self._status_receiver: ServiceBusReceiver = None

    @property
    def client(self) -> ServiceBusClient:
        return self._client

    @property
    def sender(self) -> ServiceBusSender:
        if not self._sender:
            self._sender = self._client.get_topic_sender(
                topic_name=self.settings.servicebus_topic,
                client_identifier=self.component.value)
        return self._sender

    @property
    def status_sender(self) -> ServiceBusSender:
        if not self._status_sender:
            self._status_sender = self._client.get_queue_sender(
                queue_name=self.settings.servicebus_status_queue,
                client_identifier=self.component.value)

        return self._status_sender

    @property
    def receiver(self) -> ServiceBusReceiver:
        if not self._receiver:
            self._receiver = self._client.get_subscription_receiver(
                topic_name=self.settings.servicebus_topic,
                subscription_name=self.settings.servicebus_subscription,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=self.component.value)

        return self._receiver

    @property
    def status_receiver(self) -> ServiceBusReceiver:
        if not self._status_receiver:
            self._status_receiver = self._client.get_queue_receiver(
                queue_name=self.settings.servicebus_status_queue,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=self.component.value)

        return self._status_receiver


    async def close(self):
        if self._credential:
            await self._credential.close()
        if self._client:
            await self._client.close()

    async def send_status_message(self, tag: StatusTagEnum, value: bool, correlation_id: str = None):
        message = StatusMessage(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            data=MessageStatusData(
                source=self.component,
                tag=tag,
                value=value
            ))

        logging.info(f"Send status: source: {message.data.source}, status tag: {tag}, value: {value}")
        await self.send_message(message, True)

    async def send_message(self, message: Message, status:bool = False):
        logging.info(f"Send message: {message.id} to queue: { 'status' if status else 'data' }")

        sender = self.status_sender if status else self.sender

        # Add trace baggage fom current runtime context
        app_props: dict = {}
        propagate.inject(app_props)

        await sender.send_messages(toServiceBusMessage(message, {"baggage": app_props["baggage"]}))

    async def receive_messages(self, processor: Callable[[Message], Awaitable], status:bool = False):
        try:
            receiver = self.status_receiver if status else self.receiver
            queue_msg: ServiceBusReceivedMessage = None

            ctx_token = None

            async for queue_msg in receiver:
                try:
                    # Get trace baggage fom message and inject to current runtime context

                    remote_ctx = propagate.extract(self.to_string_dict(queue_msg.application_properties))
                    ctx_token = context.attach(remote_ctx)

                    #baggage_data = dict(baggage.get_all(remote_ctx))
                    # if baggage_data:
                    #     updated_ctx = None
                    #     for k,v in baggage_data.items():
                    #         updated_ctx = baggage.set_baggage(name=k, value=v, context=updated_ctx)

                    #     ctx_token = context.attach(updated_ctx)

                    # Process message
                    message = fromServiceBusMessage(queue_msg)
                    if status:
                        message = StatusMessage.model_validate(message.model_dump())

                    logging.info(f"Received message: id: {message.id} from queue: { 'status' if status else 'data' }")
                    await processor(message)

                    await receiver.complete_message(queue_msg)
                except (MessageLockLostError, SessionLockLostError, MessageAlreadySettled):
                    logging.exception("Recoverable error in queue handler in complete_message()")
                finally:
                    if ctx_token:
                        context.detach(ctx_token)

        except asyncio.CancelledError:
            logging.info("Queue receiver task canceled")

        except Exception as e:
            logging.exception("Error in queue message handler")
            raise e

    @staticmethod
    def to_string_dict(src: Mapping) -> dict[str,str]:
        ret = {}
        for k,v in src.items():
            nk = k.decode() if isinstance(k, bytes) else str(k)                 # type: ignore
            nv: str = v.decode() if isinstance(v, bytes) else str(v)            # type: ignore
            ret[nk] = nv
        return ret

def toServiceBusMessage(m: Message, application_properties: dict = None) -> ServiceBusMessage:
    return ServiceBusMessage(
        body=m.data.model_dump_json() if isinstance(m.data, BaseModel) else json.dumps(m.data),
        content_type="application/json",
        message_id=m.id,
        correlation_id=m.correlation_id,
        application_properties=application_properties or {}
    )

def fromServiceBusMessage(msg: ServiceBusReceivedMessage) -> Message:
    return Message(
        id=msg.message_id,
        correlation_id=msg.correlation_id,
        data=json.loads(next(msg.body).decode('utf-8'))
    )
