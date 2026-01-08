import logging
import os
import json
import glob
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone, timedelta

LOG_DIR = "logs"
LOG_FILE = "Chat_api.log"
LOG_RETENTION_DAYS = 5


# ✅ == Verify the logs directory exists ==
os.makedirs(LOG_DIR, exist_ok=True)


# ✅ == JSON Log Formatter ==
class JSONFormatter(logging.Formatter):

    """
    Structured JSON formatter for logs.
    Designed for ELK/LOKI/OpenSearch compatibility
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno,
            "funcName": record.funcName,
        }

        # Adding exceptional details if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


# ===✅ Log Cleanup ===
def cleanup_old_logs(
    log_dir: str,
    retention_days: int
) -> None:
    """
    Deletes log files older than retention_days.
    Required because TimedRotatingFileHandler
    only cleans up on rotation, NOT on startup.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days)

    for path in glob.glob(os.path.join(log_dir, "*.log*")):
        try:
            mtime = datetime.fromtimestamp(
                os.path.getmtime(path), timezone.utc)
            if mtime < cutoff_time:
                os.remove(path)
        except Exception as exc:
            logging.warning(
                "Failed to delete old log file %s: %s", path, exc
            )


# ===✅ Log Setup ===
def setup_logging():
    """
   Global logging setup:
    - JSON file logging
    - Console logging
    - Daily rotation at UTC midnight
    - Guaranteed 5-day retention
    """

   # 🔥 Ensure cleanup ALWAYS happens on startup
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Prevent duplicate handlers on reload
    if root_logger.handlers:
        return

    # == File Handler ==
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, LOG_FILE),
        when="midnight",
        interval=1,
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
        utc=True,       # IMPORTANT: rotate based on UTC
        delay=True      # File opens only when first log is written
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())

    # == Console Handler ==
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    # == Attach Handlers ==
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("✅ Logging system initialized.")
