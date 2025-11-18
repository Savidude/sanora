"""logger config"""

import logging
import os
import sys


def configure_logger(name: str) -> logging.Logger:
    """sets default logger config"""
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOGGING_LEVEL") or logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter("%(levelname)-10s%(message)s")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger
