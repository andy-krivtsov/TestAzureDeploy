'''
Test application
'''

import logging
from typing import Any, Type
from fastapi import Depends, FastAPI, Request

class DemoService:
    def __init__(self, data):
        self._data = data

    @property
    def data(self) -> str:
        return self._data

class DemoService2:
    def __init__(self, data):
        self._data = data

    @property
    def data(self) -> str:
        return self._data


async def lifespan(app: FastAPI):
    logging.info("Demo app init!")

    services: dict[Type, Any] = {}
    services[DemoService] = DemoService("Service Data xxxxxx")
    services[DemoService2] = DemoService2("Some other data")

    app.state.services = services

    yield
    logging.info("Demo app shutdown!")

def get_demo_service() -> DemoService:
    return app.state.services[DemoService]

def get_service(service_type: Type) -> Any:
    return lambda: app.state.services[service_type]

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def get_root(
            request: Request,
            srv: DemoService = Depends(get_service(DemoService)),
            srv2: DemoService2 = Depends(get_service(DemoService2))
        ):
    return {
        "title": "Test FastAPI application!",
        "service_data": srv.data,
        "service2_data": srv2.data
    }

