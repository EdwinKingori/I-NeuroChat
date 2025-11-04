import logging
import os
import json
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone

LOG_DIR = "logs"
LOG_FILE = "Chat_api.log"


# Verify the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)


# JSON log formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.name,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno,
            "funcName": record.funcName,
        }

        # Adding exceptional details if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


# Configure the global logging
def setup_logging():
    """
    Setting up the global logging with both JSON file logging and
    human-readable console logging, with auto-rotation and 5-day retention.
    """

    # log_formatter = logging.Formatter(
    #     "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S"
    # )

    log_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, LOG_FILE),
        when="midnight",  # should rotate every midnight
        interval=1,
        backupCount=5,  # keep 5 days of log
        encoding="utf-8"
    )
    json_formatter = JSONFormatter()
    log_handler.setFormatter(json_formatter)
    log_handler.setLevel(logging.INFO)

    # root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(log_handler)

    # Print log to the console
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    logging.info("✅ Logging system initialized.")
