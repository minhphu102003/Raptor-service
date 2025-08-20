from datetime import time as dtime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def timed_handler_factory(filename: str, when: str = "midnight", backupCount: int = 7):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    h = TimedRotatingFileHandler(
        filename=filename,
        when=when,
        interval=1,
        backupCount=backupCount,
        encoding="utf-8",
        utc=False,
        atTime=dtime(0, 0, 0),
    )

    def namer(default_name: str) -> str:
        base, sep, date = default_name.rpartition(".log.")
        return f"{base}-{date}.log" if sep else default_name

    h.namer = namer
    return h
