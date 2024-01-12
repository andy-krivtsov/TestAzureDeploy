'''
Test demo application

Application runs as user-facing WebApp
'''
import logging
from asyncio import Task, create_task
from typing import Any

from fastapi import FastAPI

from demoapp.app import AppBuilder
from demoapp.models import ComponentsEnum
from demoapp.controllers.testapp import router


app = AppBuilder(ComponentsEnum.front_service) \
        .with_static() \
        .with_appinsights(False) \
        .with_healthprobes(False) \
        .build()

app.include_router(router)

