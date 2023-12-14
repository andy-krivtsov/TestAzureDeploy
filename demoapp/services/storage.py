from __future__ import annotations

import logging

from azure.identity.aio import ClientSecretCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import BlobType, ContentSettings
from demoapp.models import Message

from demoapp.settings import AppSettings

class StorageService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

        credential = ClientSecretCredential(
            tenant_id=settings.auth_tenant_id,
            client_id=settings.auth_client_id,
            client_secret=settings.auth_client_secret)

        self.client = BlobServiceClient(
            account_url=settings.storage_url,
            credential=credential)

    async def close(self):
        await self.client.close()

    async def save_message(self, message: Message):
        logging.info("Save message: %s to blob storage", message.id)

        if not message.id:
            raise ValueError("Message ID can't be None!")

        blob = self.client.get_blob_client(
            container=self.settings.storage_container,
            blob=f"{message.id}.json")

        props = await blob.upload_blob(
            data=message.model_dump_json(indent=2),
            blob_type=BlobType.BLOCKBLOB,
            overwrite=True,
            content_settings=ContentSettings(
                content_type="application/json",
                content_encoding="utf-8"
            ))

        logging.info("Saved blob properties: %s", props)
