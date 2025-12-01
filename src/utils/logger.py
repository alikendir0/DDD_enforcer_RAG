"""
Centralized logging configuration for the RAG Chatbot system.
"""
import logging
import sys
from pathlib import Path

from config.settings import LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with consistent formatting.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL))

        # Formatter
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for a module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance
    """
    return setup_logger(name)
