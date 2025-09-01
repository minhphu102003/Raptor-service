from contextlib import contextmanager
import time


@contextmanager
def pacer(min_interval_sec: float):
    t0 = time.monotonic()
    try:
        yield
    finally:
        dt = time.monotonic() - t0
        remain = min_interval_sec - dt
        if remain > 0:
            time.sleep(remain)
