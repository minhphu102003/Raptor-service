import asyncio
import statistics

from starlette.middleware.base import BaseHTTPMiddleware


class LoopLagMonitor:
    def __init__(self, interval=0.1):
        self.interval = interval
        self._last = None
        self.p95 = 0.0  # ms
        self._samples = []

    async def run(self):
        loop = asyncio.get_running_loop()
        self._last = loop.time()
        while True:
            await asyncio.sleep(self.interval)
            now = loop.time()
            # kỳ vọng now - last ≈ interval
            lag = max(0.0, (now - self._last) - self.interval) * 1000.0  # ms
            self._samples.append(lag)
            if len(self._samples) > 200:  # ~20s cửa sổ
                self._samples.pop(0)
            self.p95 = (
                statistics.quantiles(self._samples, n=20)[-1] if len(self._samples) >= 20 else lag
            )
            self._last = now


class AddLagHeaderMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, monitor: LoopLagMonitor):
        super().__init__(app)
        self.monitor = monitor

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Event-Loop-Lag-p95-ms"] = f"{self.monitor.p95:.2f}"
        return response
