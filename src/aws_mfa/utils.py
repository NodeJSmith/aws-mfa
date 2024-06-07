import sys

from loguru import logger


def log_error_and_exit(message: str | Exception):
    """Log an error message and exit with error"""
    logger.error(message)
    sys.exit(1)
