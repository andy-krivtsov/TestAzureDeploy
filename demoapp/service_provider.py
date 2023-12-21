
from typing import Any, Type


class ServiceProvider(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ServiceProvider, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, "services"):
            self.services: dict[Type, Any] = {}

    def register(self, service_type: Type, service: Any):
        self.services[service_type] = service

    def get_service(self, service_type: Type) -> Any:
        return self.services.get(service_type, None)