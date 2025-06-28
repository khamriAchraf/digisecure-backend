import logging
import sys

LOGGER_NAME = "app"

# Create a custom logger
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
formatter = logging.Formatter(
    "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"
)
console_handler.setFormatter(formatter)

# Add handlers to the logger if not already added
if not logger.hasHandlers():
    logger.addHandler(console_handler)
