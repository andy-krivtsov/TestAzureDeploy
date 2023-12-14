import logging
import sys
from uvicorn.logging import AccessFormatter, ColourizedFormatter
from demoapp.settings import AppSettings

def setup_logging(settings: AppSettings) -> None:
    # Root logger
    logger = logging.getLogger()
    logger.handlers.clear()
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


    # Azure SDK loggers
    azure_logger = logging.getLogger("azure")
    azure_logger.setLevel(logging.WARNING)