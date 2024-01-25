import asyncio
import logging
from typing import Any
import uuid

from azure.identity.aio import ClientSecretCredential
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver
from azure.servicebus import ServiceBusReceiveMode, ServiceBusReceivedMessage, ServiceBusMessage
from azure.servicebus.exceptions import MessageLockLostError, SessionLockLostError, MessageAlreadySettled

from demoapp.app.sp import ServiceProvider
from demoapp.services.settings import AppSettings
from demoapp.services.message_base import MessageServiceBase
from demoapp.models import Order, OrderStatusUpdate
from pydantic import BaseModel


class ServiceBusMessageService(MessageServiceBase):

    def __init__(self, sp: ServiceProvider):
        super().__init__(sp)

        settings: AppSettings = sp.get_service(AppSettings)
        credential: ClientSecretCredential = sp.get_service(ClientSecretCredential)

        self._client = ServiceBusClient(settings.servicebus_namespace, credential)

        # Order messages: send & receive
        self._order_sender = self._client.get_topic_sender(
            topic_name=settings.servicebus_orders_topic,
            client_identifier=settings.otel_service_name)

        if settings.servicebus_orders_sub:
            self._order_receiver = self._client.get_subscription_receiver(
                topic_name=settings.servicebus_orders_topic,
                subscription_name=settings.servicebus_orders_sub,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=settings.otel_service_name)

            self._order_receiver_task = asyncio.create_task(self._background_order_receiver())

        else:
            self._order_receiver = None
            self._order_receiver_task = None

        # Status messages: send & receive
        self._status_sender = self._client.get_topic_sender(
            topic_name=settings.servicebus_status_topic,
            client_identifier=settings.otel_service_name)

        if settings.servicebus_status_sub:
            self._status_receiver = self._client.get_subscription_receiver(
                topic_name=settings.servicebus_status_topic,
                subscription_name=settings.servicebus_status_sub,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                client_identifier=settings.otel_service_name)

            self._status_receiver_task = asyncio.create_task(self._background_status_receiver())
        else:
            self._status_receiver = None
            self._status_receiver_task = None

    async def close(self):
        await super().close()
        if self._order_receiver_task:
            self._order_receiver_task.cancel()

        if self._status_receiver_task:
            self._status_receiver_task.cancel()

        await self._client.close()

    async def send_processing_message(self, order: Order):
        if not self._order_sender:
            raise Exception("Service Bus processing topic is not configured!")

        message_id = str(uuid.uuid4())
        logging.info("Send order processing message: order_id: %s, message_id: %s", order.id, message_id)

        await self._order_sender.send_messages(ServiceBusMessage(
            body=order.model_dump_json(by_alias=True),
            content_type="application/json",
            message_id=message_id
        ))

    async def send_status_message(self, update: OrderStatusUpdate):
        if not self._status_sender:
            raise Exception("Service Bus status topic is not configured!")

        message_id = str(uuid.uuid4())
        logging.info("Send status update message: order_id: %s, message_id: %s", update.order_id, message_id)

        await self._status_sender.send_messages(ServiceBusMessage(
            body=update.model_dump_json(by_alias=True),
            content_type="application/json",
            message_id=message_id
        ))

    async def _background_order_receiver(self):
        if not self._order_receiver:
            raise Exception("Service Bus order receiver is not configured!")

        logging.info("Start receiving of order processing messages from Service Bus topic")
        await self.topic_receiver(self._order_receiver, Order)

    async def _background_status_receiver(self):
        if not self._status_receiver:
            raise Exception("Service Bus status receiver is not configured!")

        logging.info("Start receiving of order status update messages from Service Bus topic")
        await self.topic_receiver(self._status_receiver, OrderStatusUpdate)

    async def topic_receiver(self, receiver: ServiceBusReceiver, model_type: type):
        try:
            bus_msg: ServiceBusReceivedMessage = None

            async for bus_msg in receiver:
                try:
                    obj = self._receivedMessageToModel(bus_msg, model_type)
                    self._logReceivedObj(obj, bus_msg.message_id)

                    await self._process_message(obj)

                    await receiver.complete_message(bus_msg)
                except (MessageLockLostError, SessionLockLostError, MessageAlreadySettled):
                    logging.exception("Recoverable error in topic receiver. Continue to next message")

        except asyncio.CancelledError:
            logging.info("Service Bus background receiving coroutine (%s) is canceled!", model_type.__name__)

    async def _process_message(self, obj: BaseModel):
        if isinstance(obj, Order):
             await self._process_order(obj)
        elif isinstance(obj, OrderStatusUpdate):
            await self._process_status_update(obj)
        else:
            ValueError("Incorrect received message type!")

    @staticmethod
    def _logReceivedObj(obj: BaseModel, message_id: str):
        if isinstance(obj, Order):
            logging.info("Received order processing message: order_id: %s, message_id: %s", obj.id, message_id)
        elif isinstance(obj, OrderStatusUpdate):
            logging.info("Received order status update: order_id: %s, message_id: %s", obj.order_id, message_id)
        else:
            ValueError("Incorrect received message type!")

    @staticmethod
    def _receivedMessageToModel(msg: ServiceBusReceivedMessage, model_type: type) -> Any:
        try:
            data = next(msg.body).decode('utf-8')
            return model_type.model_validate_json(data)   #type: ignore
        except Exception as exc:
            logging.exception("Error in object cobversion _receivedMessageToModel()")
