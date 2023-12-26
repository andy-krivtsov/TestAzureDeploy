
from typing import Any, Type


class ServiceProvider:
    def __init__(self):
        self._services: dict[Type, Any] = {}

    def register(self, service_type: Type, instance: Any = None):
        if instance:
            self._services[service_type] = instance
        else:
            self._services[service_type] = service_type()

    def unregister(self, service_type: Type):
        del self._services[service_type]

    def get_service(self, service_type: Type) -> Any:
        return self._services.get(service_type, None)

    def __setitem__ (self, key: Type, value: Any) -> None:
        self._services[key] = value

    def __getitem__(self, key: Type) -> Any:
        self._services[key]

    def __delitem__(self, key: Type) -> None:
        del self._services[key]

