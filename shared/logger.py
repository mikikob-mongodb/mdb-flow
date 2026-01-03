"""Logging configuration for Flow Companion.

Provides centralized logging with both console and file output for debugging.
"""

import logging
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging format
LOG_FORMAT = '%(asctime)s | %(name)-15s | %(levelname)-7s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),  # Print to terminal
        logging.FileHandler(f'logs/flow_companion_{datetime.now().strftime("%Y%m%d")}.log')  # Daily log file
    ]
)

# Set external libraries to WARNING to reduce noise
logging.getLogger('anthropic').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('voyageai').setLevel(logging.WARNING)
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
