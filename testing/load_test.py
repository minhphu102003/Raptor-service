from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import statistics
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

from db.providers.base import IDatabaseProvider
from uow.sqlalchemy_uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Result of a load test"""

    provider_name: str
    test_name: str
    duration_seconds: float
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    median_response_time_ms: float
    percentile_95_ms: float
    percentile_99_ms: float
    error_rate: float
    errors: List[str] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "provider_name": self.provider_name,
            "test_name": self.test_name,
            "duration_seconds": self.duration_seconds,
            "concurrent_users": self.concurrent_users,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "requests_per_second": self.requests_per_second,
            "avg_response_time_ms": self.avg_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms,
            "max_response_time_ms": self.max_response_time_ms,
            "median_response_time_ms": self.median_response_time_ms,
            "percentile_95_ms": self.percentile_95_ms,
            "percentile_99_ms": self.percentile_99_ms,
            "error_rate": self.error_rate,
            "errors": self.errors[:10],  # Limit errors in output
            "metadata": self.metadata,
        }


class LoadTester:
    """Load tester for database providers"""

    def __init__(self, provider: IDatabaseProvider):
        self.provider = provider
        self.provider_name = provider.provider_name

    async def run_constant_load_test(
        self,
        test_name: str,
        duration_seconds: int,
        concurrent_users: int,
        operation_func: Optional[Callable[[], Awaitable[Any]]] = None,
    ) -> LoadTestResult:
        """Run a constant load test for the specified duration"""

        if operation_func is None:
            operation_func = self._default_operation

        logger.info(
            f"Starting load test '{test_name}' on {self.provider_name}: "
            f"{concurrent_users} users for {duration_seconds}s"
        )

        # Shared state for workers
        test_state = {
            "start_time": time.time(),
            "end_time": 0,
            "stop_flag": False,
            "results": [],
            "errors": [],
        }

        test_state["end_time"] = test_state["start_time"] + duration_seconds

        # Start concurrent workers
        tasks = []
        for worker_id in range(concurrent_users):
            task = asyncio.create_task(
                self._load_test_worker(worker_id, test_state, operation_func)
            )
            tasks.append(task)

        # Wait for all workers to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        return self._analyze_load_test_results(
            test_name=test_name,
            duration_seconds=duration_seconds,
            concurrent_users=concurrent_users,
            results=test_state["results"],
            errors=test_state["errors"],
        )

    async def run_ramp_up_test(
        self,
        test_name: str,
        max_users: int,
        ramp_up_duration: int,
        test_duration: int,
        operation_func: Optional[Callable[[], Awaitable[Any]]] = None,
    ) -> List[LoadTestResult]:
        """Run a ramp-up load test, gradually increasing users"""

        if operation_func is None:
            operation_func = self._default_operation

        results = []
        user_increments = [1, 5, 10, 25, 50, max_users]
        user_increments = [u for u in user_increments if u <= max_users]

        logger.info(
            f"Starting ramp-up test '{test_name}' on {self.provider_name}: "
            f"0 -> {max_users} users over {ramp_up_duration}s"
        )

        for user_count in user_increments:
            if user_count > max_users:
                continue

            logger.info(f"Testing with {user_count} concurrent users...")

            result = await self.run_constant_load_test(
                test_name=f"{test_name}_ramp_{user_count}",
                duration_seconds=test_duration,
                concurrent_users=user_count,
                operation_func=operation_func,
            )

            results.append(result)

            # Brief pause between ramp steps
            await asyncio.sleep(1)

        return results

    async def run_spike_test(
        self,
        test_name: str,
        normal_users: int,
        spike_users: int,
        spike_duration: int,
        total_duration: int,
        operation_func: Optional[Callable[[], Awaitable[Any]]] = None,
    ) -> List[LoadTestResult]:
        """Run a spike test with sudden load increases"""

        if operation_func is None:
            operation_func = self._default_operation

        results = []

        # Phase 1: Normal load
        logger.info(
            f"Spike test phase 1: {normal_users} users for {(total_duration - spike_duration) // 2}s"
        )
        result1 = await self.run_constant_load_test(
            test_name=f"{test_name}_normal_1",
            duration_seconds=(total_duration - spike_duration) // 2,
            concurrent_users=normal_users,
            operation_func=operation_func,
        )
        results.append(result1)

        # Phase 2: Spike load
        logger.info(f"Spike test phase 2: {spike_users} users for {spike_duration}s")
        result2 = await self.run_constant_load_test(
            test_name=f"{test_name}_spike",
            duration_seconds=spike_duration,
            concurrent_users=spike_users,
            operation_func=operation_func,
        )
        results.append(result2)

        # Phase 3: Back to normal
        logger.info(
            f"Spike test phase 3: {normal_users} users for {(total_duration - spike_duration) // 2}s"
        )
        result3 = await self.run_constant_load_test(
            test_name=f"{test_name}_normal_2",
            duration_seconds=(total_duration - spike_duration) // 2,
            concurrent_users=normal_users,
            operation_func=operation_func,
        )
        results.append(result3)

        return results

    async def _load_test_worker(
        self,
        worker_id: int,
        test_state: Dict[str, Any],
        operation_func: Callable[[], Awaitable[Any]],
    ) -> None:
        """Individual worker for load testing"""

        worker_results = []
        worker_errors = []

        while time.time() < test_state["end_time"] and not test_state["stop_flag"]:
            try:
                start_time = time.time()
                await operation_func()
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                worker_results.append(
                    {
                        "worker_id": worker_id,
                        "timestamp": start_time,
                        "response_time_ms": response_time_ms,
                        "success": True,
                    }
                )

            except Exception as e:
                worker_errors.append(
                    {
                        "worker_id": worker_id,
                        "timestamp": time.time(),
                        "error": str(e),
                        "success": False,
                    }
                )

            # Small delay to prevent overwhelming the database
            await asyncio.sleep(0.001)

        # Add worker results to shared state (thread-safe in asyncio)
        test_state["results"].extend(worker_results)
        test_state["errors"].extend(worker_errors)

    def _analyze_load_test_results(
        self,
        test_name: str,
        duration_seconds: int,
        concurrent_users: int,
        results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
    ) -> LoadTestResult:
        """Analyze load test results and create summary"""

        successful_requests = len(results)
        failed_requests = len(errors)
        total_requests = successful_requests + failed_requests

        if successful_requests > 0:
            response_times = [r["response_time_ms"] for r in results]
            response_times.sort()

            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = statistics.median(response_times)

            # Calculate percentiles
            p95_index = int(0.95 * len(response_times))
            p99_index = int(0.99 * len(response_times))
            percentile_95 = response_times[min(p95_index, len(response_times) - 1)]
            percentile_99 = response_times[min(p99_index, len(response_times) - 1)]
        else:
            response_times = []
            avg_response_time = 0.0
            min_response_time = 0.0
            max_response_time = 0.0
            median_response_time = 0.0
            percentile_95 = 0.0
            percentile_99 = 0.0

        requests_per_second = total_requests / duration_seconds if duration_seconds > 0 else 0.0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0

        error_messages = [e["error"] for e in errors]

        return LoadTestResult(
            provider_name=self.provider_name,
            test_name=test_name,
            duration_seconds=duration_seconds,
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=requests_per_second,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            median_response_time_ms=median_response_time,
            percentile_95_ms=percentile_95,
            percentile_99_ms=percentile_99,
            error_rate=error_rate,
            errors=error_messages,
            response_times=response_times,
        )

    async def _default_operation(self) -> None:
        """Default operation for load testing - simple query"""
        uow = SqlAlchemyUnitOfWork.from_provider(self.provider)
        async with uow:
            if hasattr(uow.session, "execute"):
                from sqlalchemy import text

                await uow.session.execute(text("SELECT 1"))

    async def create_document_operation(self) -> Callable[[], Awaitable[Any]]:
        """Create an operation that simulates document creation"""
        counter = {"value": 0}

        async def operation():
            counter["value"] += 1
            doc_id = f"load_test_doc_{counter['value']}_{time.time()}"

            uow = SqlAlchemyUnitOfWork.from_provider(self.provider)
            async with uow:
                if hasattr(uow.session, "execute"):
                    from sqlalchemy import text

                    # Simulate document insertion
                    await uow.session.execute(
                        text("SELECT 1 WHERE :doc_id IS NOT NULL"), {"doc_id": doc_id}
                    )

        return operation

    async def create_query_operation(self, query: str) -> Callable[[], Awaitable[Any]]:
        """Create an operation that executes a custom query"""

        async def operation():
            uow = SqlAlchemyUnitOfWork.from_provider(self.provider)
            async with uow:
                if hasattr(uow.session, "execute"):
                    from sqlalchemy import text

                    await uow.session.execute(text(query))

        return operation
