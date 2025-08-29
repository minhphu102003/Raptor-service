from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import statistics
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

from db.providers.base import IDatabaseProvider
from uow.abstract_uow import AbstractUnitOfWork
from uow.sqlalchemy_uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""

    test_name: str
    provider_name: str
    execution_times: List[float]  # in milliseconds
    success_count: int
    error_count: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def avg_time(self) -> float:
        """Average execution time in milliseconds"""
        return statistics.mean(self.execution_times) if self.execution_times else 0.0

    @property
    def min_time(self) -> float:
        """Minimum execution time in milliseconds"""
        return min(self.execution_times) if self.execution_times else 0.0

    @property
    def max_time(self) -> float:
        """Maximum execution time in milliseconds"""
        return max(self.execution_times) if self.execution_times else 0.0

    @property
    def median_time(self) -> float:
        """Median execution time in milliseconds"""
        return statistics.median(self.execution_times) if self.execution_times else 0.0

    @property
    def std_dev(self) -> float:
        """Standard deviation of execution times"""
        return statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0

    @property
    def percentile_95(self) -> float:
        """95th percentile of execution times"""
        if not self.execution_times:
            return 0.0
        sorted_times = sorted(self.execution_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "test_name": self.test_name,
            "provider_name": self.provider_name,
            "execution_times": self.execution_times,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "errors": self.errors,
            "metadata": self.metadata,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "median_time": self.median_time,
            "std_dev": self.std_dev,
            "percentile_95": self.percentile_95,
            "success_rate": self.success_rate,
        }


class DatabaseBenchmark:
    """Database benchmark for testing individual operations"""

    def __init__(self, provider: IDatabaseProvider):
        self.provider = provider
        self.provider_name = provider.provider_name

    async def run_simple_query_test(self, iterations: int = 100) -> BenchmarkResult:
        """Test simple SELECT 1 query performance"""
        return await self._run_test(
            test_name="simple_query", test_func=self._simple_query, iterations=iterations
        )

    async def run_transaction_test(self, iterations: int = 50) -> BenchmarkResult:
        """Test transaction begin/commit performance"""
        return await self._run_test(
            test_name="transaction", test_func=self._transaction_test, iterations=iterations
        )

    async def run_connection_test(self, iterations: int = 20) -> BenchmarkResult:
        """Test connection creation/closure performance"""
        return await self._run_test(
            test_name="connection", test_func=self._connection_test, iterations=iterations
        )

    async def run_concurrent_query_test(
        self, concurrent_count: int = 10, iterations_per_worker: int = 10
    ) -> BenchmarkResult:
        """Test concurrent query performance"""

        async def concurrent_test():
            tasks = []
            for _ in range(concurrent_count):
                task = asyncio.create_task(self._run_concurrent_worker(iterations_per_worker))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            total_time = 0.0
            success_count = 0
            errors = []

            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                elif isinstance(result, dict):
                    total_time += result["time"]
                    success_count += result["success_count"]
                    errors.extend(result["errors"])
                else:
                    errors.append(f"Unexpected result type: {type(result)}")

            return {"time": total_time, "success_count": success_count, "errors": errors}

        return await self._run_test(
            test_name="concurrent_query",
            test_func=concurrent_test,
            iterations=1,
            metadata={
                "concurrent_count": concurrent_count,
                "iterations_per_worker": iterations_per_worker,
            },
        )

    async def _run_test(
        self,
        test_name: str,
        test_func: Callable[[], Awaitable[Any]],
        iterations: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkResult:
        """Run a benchmark test with the specified function"""
        execution_times = []
        errors = []
        success_count = 0
        error_count = 0

        logger.info(
            f"Running {test_name} test with {iterations} iterations on {self.provider_name}"
        )

        for i in range(iterations):
            try:
                start_time = time.time()
                await test_func()
                end_time = time.time()

                execution_time_ms = (end_time - start_time) * 1000
                execution_times.append(execution_time_ms)
                success_count += 1

            except Exception as e:
                error_count += 1
                error_msg = f"Iteration {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Test {test_name} iteration {i} failed: {e}")

        return BenchmarkResult(
            test_name=test_name,
            provider_name=self.provider_name,
            execution_times=execution_times,
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            metadata=metadata or {},
        )

    async def _simple_query(self):
        """Execute a simple SELECT 1 query"""
        uow = SqlAlchemyUnitOfWork.from_provider(self.provider)
        async with uow:
            # For SQLAlchemy providers, we can execute raw SQL
            if hasattr(uow.session, "execute"):
                from sqlalchemy import text

                await uow.session.execute(text("SELECT 1"))

    async def _transaction_test(self):
        """Test transaction begin/commit"""
        uow = SqlAlchemyUnitOfWork.from_provider(self.provider)
        async with uow:
            # The transaction is automatically managed by the context manager
            pass

    async def _connection_test(self):
        """Test connection creation and closure"""
        session = await self.provider.session_provider.create_session()
        try:
            # Test that the session is usable
            if hasattr(session, "execute"):
                from sqlalchemy import text

                await session.execute(text("SELECT 1"))
        finally:
            await self.provider.session_provider.close_session(session)

    async def _run_concurrent_worker(self, iterations: int) -> Dict[str, Any]:
        """Worker function for concurrent testing"""
        success_count = 0
        errors = []
        start_time = time.time()

        for _ in range(iterations):
            try:
                await self._simple_query()
                success_count += 1
            except Exception as e:
                errors.append(str(e))

        end_time = time.time()

        return {
            "time": (end_time - start_time) * 1000,
            "success_count": success_count,
            "errors": errors,
        }


class BenchmarkSuite:
    """Suite of benchmarks to run across multiple providers"""

    def __init__(self, providers: List[IDatabaseProvider]):
        self.providers = providers
        self.results: List[BenchmarkResult] = []

    async def run_all_tests(
        self,
        simple_query_iterations: int = 100,
        transaction_iterations: int = 50,
        connection_iterations: int = 20,
        concurrent_workers: int = 10,
        concurrent_iterations: int = 10,
    ) -> List[BenchmarkResult]:
        """Run all benchmark tests across all providers"""
        self.results.clear()

        for provider in self.providers:
            logger.info(f"Running benchmarks for provider: {provider.provider_name}")

            benchmark = DatabaseBenchmark(provider)

            # Run all test types
            tests = [
                benchmark.run_simple_query_test(simple_query_iterations),
                benchmark.run_transaction_test(transaction_iterations),
                benchmark.run_connection_test(connection_iterations),
                benchmark.run_concurrent_query_test(concurrent_workers, concurrent_iterations),
            ]

            # Execute tests and collect results
            for test_coro in tests:
                try:
                    result = await test_coro
                    self.results.append(result)
                    logger.info(f"Completed {result.test_name} test for {provider.provider_name}")
                except Exception as e:
                    logger.error(f"Failed to run test for {provider.provider_name}: {e}")

        return self.results

    def get_results_by_test(self, test_name: str) -> List[BenchmarkResult]:
        """Get results for a specific test across all providers"""
        return [r for r in self.results if r.test_name == test_name]

    def get_results_by_provider(self, provider_name: str) -> List[BenchmarkResult]:
        """Get all results for a specific provider"""
        return [r for r in self.results if r.provider_name == provider_name]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all benchmark results"""
        summary = {
            "total_tests": len(self.results),
            "providers": list(set(r.provider_name for r in self.results)),
            "test_types": list(set(r.test_name for r in self.results)),
            "overall_success_rate": 0.0,
            "by_provider": {},
            "by_test": {},
        }

        if self.results:
            # Overall success rate
            total_success = sum(r.success_count for r in self.results)
            total_attempts = sum(r.success_count + r.error_count for r in self.results)
            summary["overall_success_rate"] = (
                (total_success / total_attempts * 100) if total_attempts > 0 else 0.0
            )

            # Summary by provider
            for provider in summary["providers"]:
                provider_results = self.get_results_by_provider(provider)
                summary["by_provider"][provider] = {
                    "test_count": len(provider_results),
                    "avg_time": statistics.mean([r.avg_time for r in provider_results]),
                    "success_rate": statistics.mean([r.success_rate for r in provider_results]),
                }

            # Summary by test
            for test_name in summary["test_types"]:
                test_results = self.get_results_by_test(test_name)
                summary["by_test"][test_name] = {
                    "provider_count": len(test_results),
                    "avg_time": statistics.mean([r.avg_time for r in test_results]),
                    "min_time": min([r.min_time for r in test_results]),
                    "max_time": max([r.max_time for r in test_results]),
                }

        return summary
