import contextvars
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from pythonjsonlogger.json import JsonFormatter

request_id_ctx = contextvars.ContextVar(
    "request_id", default=None
)  # type: contextvars.ContextVar[str | None]
user_id_ctx = contextvars.ContextVar(
    "user_id", default=None
)  # type: contextvars.ContextVar[str | None]

SERVICE_NAME = "backend"
LOGGER_NAME = "app"
LOG_FILE = "logs/app.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 5

# Create logs directory if it doesn't exist
try:
    os.makedirs("logs", exist_ok=True)

    # Ensure the logs directory and required log files exist
    log_files = [
        "logs/app.log",
        "logs/auth.log",
        "logs/permission.log",
        "logs/connection.log",
    ]
    for log_file in log_files:
        if not os.path.exists(log_file):
            with open(log_file, "a"):
                pass
except (OSError, IOError):
    # If we can't create log files, we'll just use console logging
    pass


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get() or "-"
        record.user_id = user_id_ctx.get() or "-"
        record.service = SERVICE_NAME
        return True


class AuthLogFilter(logging.Filter):
    def filter(self, record):
        return getattr(record, "log_type", None) == "auth"


class PermissionLogFilter(logging.Filter):
    def filter(self, record):
        return getattr(record, "log_type", None) == "permission"


logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

# JSON formatter
log_format = "%(asctime)s %(levelname)s %(service)s %(request_id)s %(user_id)s %(name)s %(message)s"
json_formatter = JsonFormatter(log_format)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(json_formatter)

# Rotating file handler for all logs
try:
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(json_formatter)
except (OSError, IOError):
    # If we can't create the file handler, use a null handler
    file_handler = logging.NullHandler()

AUTH_LOG_FILE = "logs/auth.log"
try:
    auth_file_handler = RotatingFileHandler(
        AUTH_LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    auth_file_handler.setLevel(logging.INFO)
    auth_file_handler.setFormatter(json_formatter)
    auth_file_handler.addFilter(AuthLogFilter())
except (OSError, IOError):
    # If we can't create the auth file handler, use a null handler
    auth_file_handler = logging.NullHandler()

# Rotating file handler for permission logs only
PERMISSION_LOG_FILE = "logs/permission.log"
try:
    permission_file_handler = RotatingFileHandler(
        PERMISSION_LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    permission_file_handler.setLevel(logging.INFO)
    permission_file_handler.setFormatter(json_formatter)
    permission_file_handler.addFilter(PermissionLogFilter())
except (OSError, IOError):
    # If we can't create the permission file handler, use a null handler
    permission_file_handler = logging.NullHandler()

# Add context filter
context_filter = ContextFilter()
console_handler.addFilter(context_filter)
file_handler.addFilter(context_filter)
auth_file_handler.addFilter(context_filter)
permission_file_handler.addFilter(context_filter)

# Add handlers if not already present
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(auth_file_handler)
    logger.addHandler(permission_file_handler)

# Utility functions to set context


def set_request_id(request_id: str | None):
    request_id_ctx.set(request_id)


def set_user_id(user_id: str | None):
    user_id_ctx.set(user_id)


def clear_log_context():
    request_id_ctx.set(None)
    user_id_ctx.set(None)
