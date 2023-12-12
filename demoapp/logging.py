import logging
import sys
from uvicorn.logging import AccessFormatter, ColourizedFormatter
from demoapp.settings import AppSettings

def setup_logging(settings: AppSettings) -> None:
    # Root logger
    logger = logging.getLogger()
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColourizedFormatter(
        fmt="{asctime} {levelprefix}{module}: {message}",
        style="{"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Uvicorn access logger
    acc_logger = logging.getLogger("uvicorn.access")
    acc_logger.handlers[0].setFormatter(AccessFormatter(
        fmt="{asctime} {levelprefix}{message}",
        style="{"
    ))