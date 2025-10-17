# logs.py

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import os

# Ensure log directory exists
LOG_FILE = "logs.txt"
os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)

# Create Rotating File Handler
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=50_000_000, backupCount=10, encoding='utf-8'
)

# Create Stream Handler (console)
stream_handler = logging.StreamHandler()

# Common formatter
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S"
)
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.ERROR)  # Main log level
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Reduce pyrogram log noise
logging.getLogger("pyrogram").setLevel(logging.WARNING)



