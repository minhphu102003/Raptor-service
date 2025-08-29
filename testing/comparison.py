from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import statistics
from typing import Any, Dict, List, Optional

from .benchmark import BenchmarkResult
from .load_test import LoadTestResult


@dataclass
class ComparisonReport:
    """Comprehensive comparison report between database providers"""

    timestamp: datetime
    providers: List[str]
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    load_test_results: List[LoadTestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "providers": self.providers,
            "benchmark_results": [r.to_dict() for r in self.benchmark_results],
            "load_test_results": [r.to_dict() for r in self.load_test_results],
            "summary": self.summary,
            "recommendations": self.recommendations,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, filepath: str) -> None:
        """Save report to file"""
        with open(filepath, "w") as f:
            f.write(self.to_json())


class PerformanceComparator:
    """Compare performance between different database providers"""

    def __init__(self):
        self.benchmark_results: List[BenchmarkResult] = []
        self.load_test_results: List[LoadTestResult] = []

    def add_benchmark_results(self, results: List[BenchmarkResult]) -> None:
        """Add benchmark results for comparison"""
        self.benchmark_results.extend(results)

    def add_load_test_results(self, results: List[LoadTestResult]) -> None:
        """Add load test results for comparison"""
        self.load_test_results.extend(results)

    def generate_comparison_report(self) -> ComparisonReport:
        """Generate a comprehensive comparison report"""
        providers = self._get_all_providers()

        report = ComparisonReport(
            timestamp=datetime.now(),
            providers=providers,
            benchmark_results=self.benchmark_results,
            load_test_results=self.load_test_results,
        )

        # Generate summary
        report.summary = self._generate_summary()

        # Generate recommendations
        report.recommendations = self._generate_recommendations()

        return report

    def _get_all_providers(self) -> List[str]:
        """Get list of all providers in the test results"""
        providers = set()

        for result in self.benchmark_results:
            providers.add(result.provider_name)

        for result in self.load_test_results:
            providers.add(result.provider_name)

        return sorted(list(providers))

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for comparison"""
        summary = {
            "benchmark_summary": self._summarize_benchmarks(),
            "load_test_summary": self._summarize_load_tests(),
            "overall_comparison": self._generate_overall_comparison(),
        }
        return summary

    def _summarize_benchmarks(self) -> Dict[str, Any]:
        """Summarize benchmark results"""
        if not self.benchmark_results:
            return {}

        providers = self._get_all_providers()
        test_types = list(set(r.test_name for r in self.benchmark_results))

        summary = {
            "providers": providers,
            "test_types": test_types,
            "by_provider": {},
            "by_test": {},
            "winners": {},
        }

        # Summary by provider
        for provider in providers:
            provider_results = [r for r in self.benchmark_results if r.provider_name == provider]
            if provider_results:
                summary["by_provider"][provider] = {
                    "avg_response_time": statistics.mean([r.avg_time for r in provider_results]),
                    "success_rate": statistics.mean([r.success_rate for r in provider_results]),
                    "total_tests": len(provider_results),
                }

        # Summary by test type
        for test_type in test_types:
            test_results = [r for r in self.benchmark_results if r.test_name == test_type]
            if test_results:
                summary["by_test"][test_type] = {
                    "providers_tested": len(test_results),
                    "avg_response_time": statistics.mean([r.avg_time for r in test_results]),
                    "best_provider": min(test_results, key=lambda x: x.avg_time).provider_name,
                    "worst_provider": max(test_results, key=lambda x: x.avg_time).provider_name,
                }

                summary["winners"][test_type] = min(
                    test_results, key=lambda x: x.avg_time
                ).provider_name

        return summary

    def _summarize_load_tests(self) -> Dict[str, Any]:
        """Summarize load test results"""
        if not self.load_test_results:
            return {}

        providers = self._get_all_providers()

        summary = {
            "providers": providers,
            "by_provider": {},
            "peak_performance": {},
            "stability_metrics": {},
        }

        # Summary by provider
        for provider in providers:
            provider_results = [r for r in self.load_test_results if r.provider_name == provider]
            if provider_results:
                summary["by_provider"][provider] = {
                    "avg_rps": statistics.mean([r.requests_per_second for r in provider_results]),
                    "avg_response_time": statistics.mean(
                        [r.avg_response_time_ms for r in provider_results]
                    ),
                    "avg_error_rate": statistics.mean([r.error_rate for r in provider_results]),
                    "max_rps": max([r.requests_per_second for r in provider_results]),
                    "min_error_rate": min([r.error_rate for r in provider_results]),
                }

        # Peak performance analysis
        if self.load_test_results:
            best_rps = max(self.load_test_results, key=lambda x: x.requests_per_second)
            best_response_time = min(self.load_test_results, key=lambda x: x.avg_response_time_ms)
            lowest_error_rate = min(self.load_test_results, key=lambda x: x.error_rate)

            summary["peak_performance"] = {
                "highest_rps": {
                    "provider": best_rps.provider_name,
                    "value": best_rps.requests_per_second,
                    "test": best_rps.test_name,
                },
                "best_response_time": {
                    "provider": best_response_time.provider_name,
                    "value": best_response_time.avg_response_time_ms,
                    "test": best_response_time.test_name,
                },
                "lowest_error_rate": {
                    "provider": lowest_error_rate.provider_name,
                    "value": lowest_error_rate.error_rate,
                    "test": lowest_error_rate.test_name,
                },
            }

        return summary

    def _generate_overall_comparison(self) -> Dict[str, Any]:
        """Generate overall comparison across all metrics"""
        providers = self._get_all_providers()
        comparison = {}

        for provider in providers:
            provider_benchmarks = [r for r in self.benchmark_results if r.provider_name == provider]
            provider_load_tests = [r for r in self.load_test_results if r.provider_name == provider]

            score = self._calculate_provider_score(provider_benchmarks, provider_load_tests)

            comparison[provider] = {
                "overall_score": score,
                "benchmark_count": len(provider_benchmarks),
                "load_test_count": len(provider_load_tests),
                "strengths": self._identify_strengths(
                    provider, provider_benchmarks, provider_load_tests
                ),
                "weaknesses": self._identify_weaknesses(
                    provider, provider_benchmarks, provider_load_tests
                ),
            }

        return comparison

    def _calculate_provider_score(
        self, benchmarks: List[BenchmarkResult], load_tests: List[LoadTestResult]
    ) -> float:
        """Calculate an overall score for a provider (0-100)"""
        score = 50.0  # Base score

        # Benchmark scoring (40% of total)
        if benchmarks:
            avg_response_time = statistics.mean([r.avg_time for r in benchmarks])
            avg_success_rate = statistics.mean([r.success_rate for r in benchmarks])

            # Lower response time is better (subtract from score)
            response_time_penalty = min(avg_response_time / 10, 20)  # Max 20 point penalty
            score -= response_time_penalty

            # Higher success rate is better
            success_bonus = (avg_success_rate - 50) / 2  # 50% success = no bonus/penalty
            score += success_bonus

        # Load test scoring (60% of total)
        if load_tests:
            avg_rps = statistics.mean([r.requests_per_second for r in load_tests])
            avg_error_rate = statistics.mean([r.error_rate for r in load_tests])
            avg_response_time = statistics.mean([r.avg_response_time_ms for r in load_tests])

            # Higher RPS is better
            rps_bonus = min(avg_rps / 10, 25)  # Max 25 point bonus
            score += rps_bonus

            # Lower error rate is better
            error_penalty = avg_error_rate / 2  # 10% error rate = 5 point penalty
            score -= error_penalty

            # Lower response time is better
            response_time_penalty = min(avg_response_time / 50, 15)  # Max 15 point penalty
            score -= response_time_penalty

        return max(0, min(100, score))

    def _identify_strengths(
        self, provider: str, benchmarks: List[BenchmarkResult], load_tests: List[LoadTestResult]
    ) -> List[str]:
        """Identify strengths of a provider"""
        strengths = []

        # Check if this provider wins in any benchmark tests
        benchmark_winners = {}
        for test_type in set(r.test_name for r in self.benchmark_results):
            test_results = [r for r in self.benchmark_results if r.test_name == test_type]
            if test_results:
                winner = min(test_results, key=lambda x: x.avg_time)
                benchmark_winners[test_type] = winner.provider_name

        for test_type, winner in benchmark_winners.items():
            if winner == provider:
                strengths.append(f"Best performance in {test_type}")

        # Check load test performance
        if load_tests:
            avg_error_rate = statistics.mean([r.error_rate for r in load_tests])
            if avg_error_rate < 1.0:
                strengths.append("Very low error rate under load")

            max_rps = max([r.requests_per_second for r in load_tests])
            if max_rps > 100:
                strengths.append("High throughput capability")

        return strengths

    def _identify_weaknesses(
        self, provider: str, benchmarks: List[BenchmarkResult], load_tests: List[LoadTestResult]
    ) -> List[str]:
        """Identify weaknesses of a provider"""
        weaknesses = []

        # Check benchmark performance
        if benchmarks:
            avg_success_rate = statistics.mean([r.success_rate for r in benchmarks])
            if avg_success_rate < 95:
                weaknesses.append("Lower reliability in benchmark tests")

        # Check load test performance
        if load_tests:
            avg_error_rate = statistics.mean([r.error_rate for r in load_tests])
            if avg_error_rate > 5.0:
                weaknesses.append("High error rate under load")

            avg_response_time = statistics.mean([r.avg_response_time_ms for r in load_tests])
            if avg_response_time > 1000:
                weaknesses.append("Slow response times under load")

        return weaknesses

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on the comparison"""
        recommendations = []

        if not self.benchmark_results and not self.load_test_results:
            return ["No test results available for generating recommendations"]

        providers = self._get_all_providers()
        if len(providers) < 2:
            return ["Need at least 2 providers to generate meaningful comparisons"]

        # Overall performance recommendation
        overall_scores = {}
        for provider in providers:
            provider_benchmarks = [r for r in self.benchmark_results if r.provider_name == provider]
            provider_load_tests = [r for r in self.load_test_results if r.provider_name == provider]
            overall_scores[provider] = self._calculate_provider_score(
                provider_benchmarks, provider_load_tests
            )

        best_provider = max(overall_scores.keys(), key=lambda x: overall_scores[x])
        recommendations.append(
            f"Overall best performer: {best_provider} (score: {overall_scores[best_provider]:.1f})"
        )

        # Specific use case recommendations
        if self.benchmark_results:
            # Find best for simple queries
            simple_query_results = [
                r for r in self.benchmark_results if "simple" in r.test_name.lower()
            ]
            if simple_query_results:
                best_simple = min(simple_query_results, key=lambda x: x.avg_time)
                recommendations.append(f"Best for simple queries: {best_simple.provider_name}")

            # Find best for transactions
            transaction_results = [
                r for r in self.benchmark_results if "transaction" in r.test_name.lower()
            ]
            if transaction_results:
                best_transaction = min(transaction_results, key=lambda x: x.avg_time)
                recommendations.append(f"Best for transactions: {best_transaction.provider_name}")

        if self.load_test_results:
            # Find best for high load
            high_load_results = [r for r in self.load_test_results if r.concurrent_users >= 10]
            if high_load_results:
                best_load = min(high_load_results, key=lambda x: x.avg_response_time_ms)
                recommendations.append(f"Best under high load: {best_load.provider_name}")

            # Find most reliable
            reliable_results = [r for r in self.load_test_results if r.error_rate < 5.0]
            if reliable_results:
                most_reliable = min(reliable_results, key=lambda x: x.error_rate)
                recommendations.append(f"Most reliable: {most_reliable.provider_name}")

        return recommendations

    def print_summary(self) -> None:
        """Print a formatted summary to console"""
        report = self.generate_comparison_report()

        print("\n" + "=" * 80)
        print("DATABASE PERFORMANCE COMPARISON REPORT")
        print("=" * 80)
        print(f"Generated: {report.timestamp}")
        print(f"Providers tested: {', '.join(report.providers)}")

        # Benchmark summary
        if report.summary.get("benchmark_summary"):
            print("\nBENCHMARK RESULTS:")
            print("-" * 40)

            bench_summary = report.summary["benchmark_summary"]
            for provider, stats in bench_summary.get("by_provider", {}).items():
                print(f"{provider}:")
                print(f"  Avg Response Time: {stats['avg_response_time']:.2f}ms")
                print(f"  Success Rate: {stats['success_rate']:.1f}%")
                print(f"  Tests Run: {stats['total_tests']}")

            print("\nWinners by test type:")
            for test_type, winner in bench_summary.get("winners", {}).items():
                print(f"  {test_type}: {winner}")

        # Load test summary
        if report.summary.get("load_test_summary"):
            print("\nLOAD TEST RESULTS:")
            print("-" * 40)

            load_summary = report.summary["load_test_summary"]
            for provider, stats in load_summary.get("by_provider", {}).items():
                print(f"{provider}:")
                print(f"  Avg RPS: {stats['avg_rps']:.1f}")
                print(f"  Avg Response Time: {stats['avg_response_time']:.2f}ms")
                print(f"  Avg Error Rate: {stats['avg_error_rate']:.2f}%")

        # Recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")

        print("\n" + "=" * 80)
