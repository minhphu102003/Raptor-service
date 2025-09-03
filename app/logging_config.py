"""Logging Configuration for RAPTOR Service

This module contains the logging configuration for the RAPTOR service application.
"""

import logging.config
from pathlib import Path


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(parents=True, exist_ok=True)

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s | %(levelname)s | %(name)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "app_daily": {
                "()": "app.logging_setup.timed_handler_factory",  # Updated import path
                "filename": "logs/app.log",
                "when": "midnight",
                "backupCount": 7,
            },
            "access_daily": {
                "()": "app.logging_setup.timed_handler_factory",  # Updated import path
                "filename": "logs/access.log",
                "when": "midnight",
                "backupCount": 7,
            },
        },
        "loggers": {
            "raptor": {"level": "INFO", "handlers": ["console", "app_daily"], "propagate": False},
            "voyage": {"level": "INFO", "handlers": ["console", "app_daily"], "propagate": False},
            "gemini": {"level": "INFO", "handlers": ["console", "app_daily"], "propagate": False},
            "storage": {"level": "INFO", "handlers": ["console", "app_daily"], "propagate": False},
            "cluster": {"level": "INFO", "handlers": ["console", "app_daily"], "propagate": False},
            "raptor.retrieve": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "raptor.chunking.langchain": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "watchfiles": {"level": "WARNING", "handlers": [], "propagate": False},
            "watchfiles.main": {"level": "WARNING", "handlers": [], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "app_daily"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "access_daily"],
                "propagate": False,
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "app_daily"]},
    }

    logging.config.dictConfig(LOGGING)
