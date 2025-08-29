# Database Decoupling and Performance Testing Guide

## Overview

This guide explains how to use the decoupled database architecture to compare performance between different database providers. The system allows you to easily switch between database providers and run comprehensive performance tests.

## Architecture

The database layer has been decoupled using the following patterns:

### 1. Provider Abstraction Pattern
- **IDatabaseProvider**: Abstract interface for all database providers
- **ISessionProvider**: Abstract interface for session management
- **DatabaseFactory**: Factory pattern for creating providers

### 2. Unit of Work Pattern
- **AbstractUnitOfWork**: Base class for transaction management
- **SqlAlchemyUnitOfWork**: SQLAlchemy-specific implementation

### 3. Dependency Injection
- **EnhancedContainer**: Multi-provider aware container
- **LegacyContainer**: Backward compatibility wrapper

## Quick Start

### 1. Configure Multiple Database Providers

Create a configuration for multiple databases:

```python
from db.config import DatabaseManagerConfig, DatabaseProviderConfig

# Create configuration
config = DatabaseManagerConfig(
    default_provider="primary",
    providers={
        "primary": DatabaseProviderConfig(
            name="primary",
            provider="postgresql",
            dsn="postgresql+psycopg://user:pass@localhost:5432/raptor_primary",
            description="Primary PostgreSQL database"
        ),
        "alternative": DatabaseProviderConfig(
            name="alternative",
            provider="postgresql_optimized",
            dsn="postgresql+psycopg://user:pass@localhost:5433/raptor_alt",
            options={"disable_prepares": True},
            description="Optimized PostgreSQL for comparison"
        )
    }
)
```

### 2. Initialize Enhanced Container

```python
from app.enhanced_container import EnhancedContainer

# Create container
container = EnhancedContainer(config)

# Initialize all providers
await container.initialize()

# Use different providers
uow_primary = container.make_uow("primary")
uow_alternative = container.make_uow("alternative")
```

### 3. Run Performance Tests

```python
from testing import BenchmarkSuite, LoadTester, PerformanceComparator

# Get providers
primary_provider = container.get_provider("primary")
alt_provider = container.get_provider("alternative")

# Run benchmarks
benchmark_suite = BenchmarkSuite([primary_provider, alt_provider])
benchmark_results = await benchmark_suite.run_all_tests()

# Run load tests
load_tester_1 = LoadTester(primary_provider)
load_tester_2 = LoadTester(alt_provider)

load_results_1 = await load_tester_1.run_constant_load_test(
    test_name="load_test",
    duration_seconds=30,
    concurrent_users=10
)

load_results_2 = await load_tester_2.run_constant_load_test(
    test_name="load_test",
    duration_seconds=30,
    concurrent_users=10
)

# Compare results
comparator = PerformanceComparator()
comparator.add_benchmark_results(benchmark_results)
comparator.add_load_test_results([load_results_1, load_results_2])

# Generate report
report = comparator.generate_comparison_report()
comparator.print_summary()

# Save report
report.save_to_file("performance_comparison.json")
```

## Available Database Providers

### 1. PostgreSQL Provider (`postgresql`)
Standard PostgreSQL provider with default SQLAlchemy settings.

```python
config = DatabaseProviderConfig(
    name="postgres",
    provider="postgresql",
    dsn="postgresql+psycopg://user:pass@host:5432/db",
    options={
        "connect_args": {
            "server_side_cursors": True
        }
    }
)
```

### 2. Supabase Provider (`supabase`)
Extends PostgreSQL provider with Supabase-specific configurations.

```python
config = DatabaseProviderConfig(
    name="supabase",
    provider="supabase",
    dsn="postgresql+psycopg://user:pass@host.supabase.co:5432/postgres",
    ssl_config={
        "sslmode": "require",
        "sslrootcert": "/path/to/ca-cert.crt"
    }
)
```

### 3. Optimized PostgreSQL Provider (`postgresql_optimized`)
High-performance PostgreSQL provider with optimized connection settings.

```python
config = DatabaseProviderConfig(
    name="optimized",
    provider="postgresql_optimized",
    dsn="postgresql+psycopg://user:pass@host:5432/db",
    options={
        "disable_prepares": True,
        "connect_args": {
            "tcp_keepalive": True,
            "statement_cache_size": 0
        }
    }
)
```

### 4. SQLite Memory Provider (`sqlite_memory`)
In-memory SQLite provider for testing and comparison.

```python
config = DatabaseProviderConfig(
    name="sqlite_test",
    provider="sqlite_memory",
    dsn="sqlite:///:memory:",  # DSN ignored for memory provider
    description="In-memory SQLite for testing"
)
```

## Performance Testing Types

### 1. Benchmark Tests

Test basic database operations:

```python
from testing.benchmark import DatabaseBenchmark

benchmark = DatabaseBenchmark(provider)

# Individual tests
simple_result = await benchmark.run_simple_query_test(iterations=100)
transaction_result = await benchmark.run_transaction_test(iterations=50)
connection_result = await benchmark.run_connection_test(iterations=20)
concurrent_result = await benchmark.run_concurrent_query_test(
    concurrent_count=10,
    iterations_per_worker=10
)
```

### 2. Load Tests

Test database under various load conditions:

```python
from testing.load_test import LoadTester

load_tester = LoadTester(provider)

# Constant load
result = await load_tester.run_constant_load_test(
    test_name="constant_load",
    duration_seconds=60,
    concurrent_users=20
)

# Ramp-up test
results = await load_tester.run_ramp_up_test(
    test_name="ramp_up",
    max_users=50,
    ramp_up_duration=30,
    test_duration=60
)

# Spike test
results = await load_tester.run_spike_test(
    test_name="spike_test",
    normal_users=10,
    spike_users=50,
    spike_duration=30,
    total_duration=120
)
```

### 3. Custom Operations

Create custom test operations:

```python
# Custom query operation
query_op = await load_tester.create_query_operation(
    "SELECT count(*) FROM documents WHERE dataset_id = 'test'"
)

result = await load_tester.run_constant_load_test(
    test_name="custom_query",
    duration_seconds=30,
    concurrent_users=5,
    operation_func=query_op
)

# Document creation operation
doc_op = await load_tester.create_document_operation()

result = await load_tester.run_constant_load_test(
    test_name="document_creation",
    duration_seconds=30,
    concurrent_users=3,
    operation_func=doc_op
)
```

## Comparison and Analysis

### Performance Metrics

The system measures various performance metrics:

**Benchmark Metrics:**
- Average response time
- Min/Max response time
- 95th percentile response time
- Standard deviation
- Success rate
- Error count and messages

**Load Test Metrics:**
- Requests per second (RPS)
- Average/Min/Max response time
- 95th/99th percentile response time
- Error rate percentage
- Total successful/failed requests
- Concurrent user capacity

### Comparison Reports

Generate comprehensive comparison reports:

```python
from testing.comparison import PerformanceComparator

comparator = PerformanceComparator()
comparator.add_benchmark_results(benchmark_results)
comparator.add_load_test_results(load_test_results)

# Generate report
report = comparator.generate_comparison_report()

# View summary
comparator.print_summary()

# Access detailed results
for provider in report.providers:
    provider_benchmarks = [r for r in report.benchmark_results
                          if r.provider_name == provider]
    print(f"{provider}: {len(provider_benchmarks)} benchmark tests")

# Save results
report.save_to_file("comparison_report.json")
```

## Example: Complete Performance Comparison

Here's a complete example comparing PostgreSQL vs Optimized PostgreSQL:

```python
import asyncio
from db.config import DatabaseManagerConfig, DatabaseProviderConfig
from app.enhanced_container import EnhancedContainer
from testing import BenchmarkSuite, LoadTester, PerformanceComparator

async def main():
    # Configuration
    config = DatabaseManagerConfig(
        default_provider="standard",
        providers={
            "standard": DatabaseProviderConfig(
                name="standard",
                provider="postgresql",
                dsn="postgresql+psycopg://user:pass@localhost:5432/raptor_db"
            ),
            "optimized": DatabaseProviderConfig(
                name="optimized",
                provider="postgresql_optimized",
                dsn="postgresql+psycopg://user:pass@localhost:5432/raptor_db",
                options={
                    "disable_prepares": True,
                    "connect_args": {
                        "tcp_keepalive": True,
                        "statement_cache_size": 0
                    }
                }
            )
        }
    )

    # Initialize container
    container = EnhancedContainer(config)
    await container.initialize()

    try:
        # Get providers
        providers = [
            container.get_provider("standard"),
            container.get_provider("optimized")
        ]

        # Run benchmark suite
        print("Running benchmark tests...")
        benchmark_suite = BenchmarkSuite(providers)
        benchmark_results = await benchmark_suite.run_all_tests(
            simple_query_iterations=200,
            transaction_iterations=100,
            connection_iterations=50,
            concurrent_workers=20,
            concurrent_iterations=20
        )

        # Run load tests
        print("Running load tests...")
        load_results = []

        for provider in providers:
            load_tester = LoadTester(provider)

            # Constant load test
            result = await load_tester.run_constant_load_test(
                test_name="constant_load",
                duration_seconds=60,
                concurrent_users=15
            )
            load_results.append(result)

            # Ramp-up test
            ramp_results = await load_tester.run_ramp_up_test(
                test_name="ramp_up",
                max_users=30,
                ramp_up_duration=60,
                test_duration=30
            )
            load_results.extend(ramp_results)

        # Compare results
        print("Analyzing results...")
        comparator = PerformanceComparator()
        comparator.add_benchmark_results(benchmark_results)
        comparator.add_load_test_results(load_results)

        # Print summary
        comparator.print_summary()

        # Generate detailed report
        report = comparator.generate_comparison_report()
        report.save_to_file("database_performance_comparison.json")

        print(f"\\nDetailed report saved to: database_performance_comparison.json")

        # Print recommendations
        print("\\nRecommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")

    finally:
        await container.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Adding New Database Providers

To add a new database provider:

### 1. Create Provider Class

```python
from db.providers.base import IDatabaseProvider, ISessionProvider
from db.providers.factory import register_provider

@register_provider("your_provider")
class YourDatabaseProvider(IDatabaseProvider):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        # Initialize your provider

    @property
    def provider_name(self) -> str:
        return "your_provider"

    @property
    def session_provider(self) -> ISessionProvider:
        return self._session_provider

    async def initialize(self) -> None:
        # Initialize connections, create session provider
        pass

    async def close(self) -> None:
        # Cleanup resources
        pass

    async def health_check(self) -> bool:
        # Test connectivity
        pass

    async def get_connection_info(self) -> Dict[str, Any]:
        # Return connection information
        pass

    async def get_performance_metrics(self) -> Dict[str, Any]:
        # Return performance metrics
        pass
```

### 2. Create Session Provider

```python
class YourSessionProvider(ISessionProvider):
    async def create_session(self) -> Any:
        # Create database session
        pass

    async def close_session(self, session: Any) -> None:
        # Close session
        pass

    async def begin_transaction(self, session: Any) -> None:
        # Begin transaction
        pass

    async def commit_transaction(self, session: Any) -> None:
        # Commit transaction
        pass

    async def rollback_transaction(self, session: Any) -> None:
        # Rollback transaction
        pass
```

### 3. Register and Use

```python
# Import your provider to register it
import your_provider_module

# Configure
config = DatabaseProviderConfig(
    name="your_db",
    provider="your_provider",
    dsn="your://connection/string"
)

# Use in container
container = EnhancedContainer(DatabaseManagerConfig(
    providers={"your_db": config}
))
```

## Best Practices

### 1. Performance Testing
- Start with small loads and gradually increase
- Run tests multiple times for consistent results
- Test under realistic data volumes
- Monitor system resources during testing

### 2. Database Configuration
- Use appropriate connection pool sizes
- Configure SSL properly for production
- Set timeouts for connection and query operations
- Monitor connection health

### 3. Comparison Analysis
- Test with similar data sets across providers
- Account for network latency differences
- Consider operational complexity in decisions
- Validate results with real-world usage patterns

### 4. Production Deployment
- Test provider switching in staging environment
- Have rollback procedures ready
- Monitor performance metrics continuously
- Document configuration differences

## Troubleshooting

### Common Issues

1. **Provider Registration Errors**
   - Ensure provider modules are imported
   - Check that `@register_provider` decorator is used
   - Verify provider names are unique

2. **Connection Issues**
   - Validate DSN format and credentials
   - Check network connectivity
   - Verify SSL configuration

3. **Performance Test Failures**
   - Reduce concurrent users for initial testing
   - Check database connection limits
   - Monitor system resources

4. **Session Management**
   - Ensure sessions are properly closed
   - Check for connection leaks
   - Monitor connection pool usage

For additional support, check the logs and enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
