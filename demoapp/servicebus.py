import logging
from typing import Awaitable, Callable
import uuid
import asyncio

from azure.identity.aio import ClientSecretCredential
from azure.servicebus.aio import ServiceBusClient, ServiceBusSender, ServiceBusReceiver
from azure.servicebus import ServiceBusReceiveMode, ServiceBusReceivedMessage
from demoapp.models import ComponentsEnum, MessageDTO, StatusData, StatusTagEnum

from demoapp.settings import AppSettings

FRONT_QUEUE_IDENTIFIER = "front-service"

class QueueService:

    def __init__(self, settings: AppSettings, component: ComponentsEnum):
        self.settings = settings
        self.component = component

        credential = ClientSecretCredential(
            tenant_id=settings.auth_tenant_id,
            client_id=settings.auth_client_id,
            client_secret=settings.auth_client_secret)

        self.client = ServiceBusClient(settings.servicebus_namespace, credential)

        self._sender: ServiceBusSender = None
        self._status_sender: ServiceBusSender = None
        self._receiver: ServiceBusReceiver = None
        self._status_receiver: ServiceBusReceiver = None

    @property
    def sender(self) -> ServiceBusSender:
        if not self._sender:
            self._sender = self.client.get_topic_sender(
                topic_name=self.settings.servicebus_topic,
                client_identifier=self.component.value)
        return self._sender

    @property
    def status_sender(self) -> ServiceBusSender:
        if not self._status_sender:
            self._status_sender = self.client.get_queue_sender(
                queue_name=self.settings.servicebus_status_queue,
                client_identifier=self.component.value)

        return self._status_sender

    @property
    def receiver(self) -> ServiceBusReceiver:
        if not self._receiver:
            self._receiver = self.client.get_subscription_receiver(
                topic_name=self.settings.servicebus_topic,
                subscription_name=self.settings.servicebus_subscription,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=self.component.value)

        return self._receiver

    @property
    def status_receiver(self) -> ServiceBusReceiver:
        if not self._status_receiver:
            self._status_receiver = self.client.get_queue_receiver(
                queue_name=self.settings.servicebus_status_queue,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=self.component.value)

        return self._status_receiver


    async def close(self):
        await self.client.close()

    async def send_status_message(self, tag: StatusTagEnum, value: bool, correlation_id: str = None):
        message = MessageDTO(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            data=StatusData(
                source=self.component,
                tag=tag,
                value=value
            ))

        logging.info(f"Send status: source: {message.data.source}, status tag: {tag}, value: {value}")
        await self.send_message(message, True)

    async def send_message(self, message: MessageDTO, status:bool = False):
        logging.info(f"Send message: {message.id} to queue: { 'status' if status else 'data' }")

        sender = self.status_sender if status else self.sender
        await sender.send_messages(message.toServiceBusMessage())

    async def receive_messages(self, processor: Callable[[MessageDTO], Awaitable], status:bool = False):
        try:
            receiver = self.status_receiver if status else self.receiver
            queue_msg: ServiceBusReceivedMessage = None

            async for queue_msg in receiver:
                message = MessageDTO.fromServiceBusMessage(queue_msg)
                if status:
                    message.data = StatusData.model_validate(message.data)

                logging.info(f"Received message: id: {message.id} from queue: { 'status' if status else 'data' }")
                await processor(message)

                await receiver.complete_message(queue_msg)
        except asyncio.CancelledError:
            logging.info("Queue receiver task canceled")

        except Exception as e:
            logging.exception("Error in queue message handler")
            raise e
