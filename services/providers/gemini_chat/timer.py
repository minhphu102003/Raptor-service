import time


class Timer:
    def __init__(self):
        self.ms = 0.0

    async def __aenter__(self):
        self._t0 = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.ms = (time.perf_counter() - self._t0) * 1e3
