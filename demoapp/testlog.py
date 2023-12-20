import logging
import sys

def log_filter(record: logging.LogRecord) -> bool:
    record.__dict__["extra3"] = "value3"
    record.__dict__["extra4"] = "value4"
    return True

logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    fmt="{asctime} {levelname:10} {module}: {message}    [{extra3}]",
    style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.addFilter(log_filter)
logger.setLevel(logging.DEBUG)

data_var1 = "test_data1"
data_var2 = 20

logging.debug("Info message: %s  %s", data_var1, data_var2, extra={"extra1": "value1", "extra2": "value2"})
logging.info("Info message: %s  %s", data_var1, data_var2)
logging.warning("Warning message")
