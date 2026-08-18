"""
utils/logger.py - Production logging with file rotation for AgroGuard-AI.
Console + rotating file handler (logs/agroguard.log, 10MB, 5 backups).
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """Return production logger with console + rotating file output."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Rotating file handler
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/agroguard.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger