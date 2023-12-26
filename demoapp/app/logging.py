
import logging
import sys
from uvicorn.logging import AccessFormatter, ColourizedFormatter

from demoapp.services import AppSettings

PROBE_FILTER = "/health"

class EndpointLoggingFilter(logging.Filter):
    def __init__(self, paths: list[str]):
        self.paths = paths

    def filter(self, record: logging.LogRecord) -> bool:
        for p in self.paths:
            if record.getMessage().find(p) != -1:
                return False
        return True


def setup_logging(settings: AppSettings) -> None:
    # Root logger
    logger = logging.getLogger()
    #logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    color_formatter = ColourizedFormatter(
        fmt="{asctime} {levelprefix}{module}: {message}",
        style="{")

    handler.setFormatter(color_formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Uvicorn loggers
    uvicorn_root = logging.getLogger("uvicorn")
    uvicorn_root.handlers[0].setFormatter(color_formatter)

    acc_logger = logging.getLogger("uvicorn.access")
    acc_logger.handlers[0].setFormatter(AccessFormatter(
        fmt="{asctime} {levelprefix}{message}",
        style="{"
    ))
    acc_logger.addFilter(EndpointLoggingFilter([PROBE_FILTER]))

    # Azure SDK loggers
    azure_logger = logging.getLogger("azure")
    azure_logger.setLevel(logging.WARNING)