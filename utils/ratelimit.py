import asyncio
from collections import deque
import time
from typing import Deque, Tuple


class RateLimiter:
    def __init__(self, rpm: int, tpm: int, window_seconds: int = 60):
        self.rpm = rpm
        self.tpm = tpm
        self.window = window_seconds
        self._req_times: Deque[float] = deque()
        self._tok_times: Deque[Tuple[float, int]] = deque()
        self._lock = asyncio.Lock()

    def _prune(self, now: float):
        cutoff = now - self.window
        while self._req_times and self._req_times[0] <= cutoff:
            self._req_times.popleft()
        while self._tok_times and self._tok_times[0][0] <= cutoff:
            self._tok_times.popleft()

    def _tokens_used(self) -> int:
        return sum(t for _, t in self._tok_times)

    async def acquire(self, tokens_for_next_req: int):
        async with self._lock:
            while True:
                now = time.monotonic()
                self._prune(now)
                req_ok = len(self._req_times) < self.rpm
                tpm_ok = (self._tokens_used() + tokens_for_next_req) <= self.tpm
                if req_ok and tpm_ok:
                    self._req_times.append(now)
                    self._tok_times.append((now, tokens_for_next_req))
                    return
                wait_req = (
                    max(0.0, self.window - (now - self._req_times[0])) if self._req_times else 0.0
                )
                wait_tok = (
                    max(0.0, self.window - (now - self._tok_times[0][0]))
                    if self._tok_times
                    else 0.0
                )
                await asyncio.sleep(max(wait_req, wait_tok, 0.1))
