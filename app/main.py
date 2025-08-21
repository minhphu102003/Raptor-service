from contextlib import asynccontextmanager
import logging
import logging.config
from pathlib import Path

from fastapi import FastAPI

from app.config import settings
from app.container import Container
from interfaces_adaptor.http.controllers import router as ingest_router


def setup_logging() -> None:
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
                "()": "app.logging_setup.timed_handler_factory",
                "filename": "logs/app.log",
                "when": "midnight",
                "backupCount": 7,
            },
            "access_daily": {
                "()": "app.logging_setup.timed_handler_factory",
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


ASYNC_DSN = settings.pg_async_dsn or settings.vector.dsn.replace(
    "postgresql://", "postgresql+asyncpg://"
)
VECTOR_DSN = settings.vector.dsn


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container(orm_async_dsn=ASYNC_DSN, vector_dsn=VECTOR_DSN)
    yield


setup_logging()
app = FastAPI(title="RAPTOR Service", lifespan=lifespan)
app.include_router(ingest_router, prefix=settings.api_prefix)
