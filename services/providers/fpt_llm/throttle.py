import random
import threading
import time
from typing import Optional


class RateLimiter:
    def __init__(self, rpm: Optional[int] = None, min_interval: Optional[float] = None):
        if rpm is not None:
            min_interval = max(min_interval or 0.0, 60.0 / float(rpm))
        self.min_interval = float(min_interval or 0.0)
        self._lock = threading.Lock()
        self._next_at = 0.0

    def acquire(self):
        if self.min_interval <= 0:
            return
        with self._lock:
            now = time.time()
            if now < self._next_at:
                time.sleep(self._next_at - now)
                now = self._next_at
            self._next_at = now + self.min_interval


class BackoffPolicy:
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 0.5,
        max_delay: float = 20.0,
        jitter: float = 0.25,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def compute_sleep(self, attempt: int, retry_after: Optional[float]) -> float:
        if retry_after is not None and retry_after >= 0:
            return float(retry_after)
        delay = min(self.base_delay * (2 ** max(0, attempt - 1)), self.max_delay)
        if self.jitter:
            delay += random.uniform(0, self.jitter)
        return delay
