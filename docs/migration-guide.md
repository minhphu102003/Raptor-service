# Migration Guide: Database Decoupling

This guide helps you migrate existing code to use the new decoupled database architecture.

## Overview of Changes

The database layer has been enhanced with:

- **Provider abstraction**: Support for multiple database types
- **Enhanced Unit of Work**: Abstract base with provider support
- **Performance testing**: Built-in benchmarking and load testing
- **Configuration management**: Multi-provider configuration system

## Backward Compatibility

**Good news**: Your existing code continues to work unchanged! The new architecture is designed for backward compatibility.

### Existing Code (Still Works)

```python
# This code continues to work as before
from app.container import Container
from db.session import build_session_factory

# Legacy usage
session_factory = build_session_factory(dsn)
container = Container(orm_async_dsn, vector_dsn)
uow = container.make_uow()
```

## Migration Options

### Option 1: Gradual Migration (Recommended)

Keep existing code but add new providers for testing:

```python
# 1. Add new imports alongside existing ones
from app.enhanced_container import EnhancedContainer
from db.config import DatabaseManagerConfig, DatabaseProviderConfig

# 2. Create enhanced container for new features
enhanced_config = DatabaseManagerConfig.create_from_legacy_settings(
    pg_async_dsn=existing_dsn,
    vector_dsn=existing_vector_dsn
)

# Add additional providers for testing
enhanced_config.add_provider("test", DatabaseProviderConfig(
    name="test",
    provider="postgresql_optimized",
    dsn=test_dsn
))

enhanced_container = EnhancedContainer(enhanced_config)
await enhanced_container.initialize()

# 3. Use enhanced features when needed
test_uow = enhanced_container.make_uow("test")
```

### Option 2: Full Migration

Replace existing container usage:

```python
# Before
from app.container import Container
container = Container(orm_async_dsn, vector_dsn)

# After
from app.enhanced_container import EnhancedContainer
from db.config import DatabaseManagerConfig

config = DatabaseManagerConfig.create_from_legacy_settings(
    pg_async_dsn=orm_async_dsn,
    vector_dsn=vector_dsn
)
container = EnhancedContainer(config)
await container.initialize()
```

## Adding Performance Testing

### Step 1: Add Test Configuration

```python
from db.config import DatabaseProviderConfig

# Add alternative provider for comparison
config.add_provider("alternative", DatabaseProviderConfig(
    name="alternative",
    provider="postgresql_optimized",
    dsn="postgresql+psycopg://user:pass@alt-host:5432/db",
    description="Alternative database for performance testing"
))
```

### Step 2: Run Performance Tests

```python
from testing import BenchmarkSuite, LoadTester, PerformanceComparator

# Get providers
primary = container.get_provider("primary")
alternative = container.get_provider("alternative")

# Run benchmarks
benchmark_suite = BenchmarkSuite([primary, alternative])
results = await benchmark_suite.run_all_tests()

# Run load tests
load_tester = LoadTester(primary)
load_results = await load_tester.run_constant_load_test(
    test_name="load_test",
    duration_seconds=60,
    concurrent_users=10
)

# Compare and analyze
comparator = PerformanceComparator()
comparator.add_benchmark_results(results)
comparator.add_load_test_results([load_results])
comparator.print_summary()
```

## Environment Configuration

### Legacy Environment Variables

These continue to work:

```bash
PG_ASYNC_DSN=postgresql+psycopg://user:pass@host:5432/db
VECTOR_DSN=postgresql+psycopg://user:pass@host:5432/db
```

### Enhanced Configuration

For multiple providers:

```bash
# Primary database
PRIMARY_DB_DSN=postgresql+psycopg://user:pass@host1:5432/db1

# Alternative database for testing
ALTERNATIVE_DB_DSN=postgresql+psycopg://user:pass@host2:5432/db2

# Performance testing settings
ENABLE_PERFORMANCE_TESTING=true
TEST_DURATION_SECONDS=60
```

## FastAPI Integration

### Existing FastAPI Code

```python
# app/main.py - existing code continues to work
from app.container import Container

async def lifespan(app: FastAPI):
    container = Container(
        orm_async_dsn=settings.pg_async_dsn,
        vector_dsn=settings.vector.dsn
    )
    app.state.container = container
    yield
```

### Enhanced FastAPI Integration

```python
# app/main.py - enhanced version
from app.enhanced_container import EnhancedContainer
from db.config import create_test_configurations

async def lifespan(app: FastAPI):
    # Create configuration
    if settings.enable_multi_db:
        config = create_test_configurations()
    else:
        config = DatabaseManagerConfig.create_from_legacy_settings(
            pg_async_dsn=settings.pg_async_dsn,
            vector_dsn=settings.vector.dsn
        )

    # Initialize container
    container = EnhancedContainer(config)
    await container.initialize()

    app.state.container = container

    yield

    # Cleanup
    await container.close()
```

## Testing Migration

### Unit Tests

Update tests to use provider abstraction:

```python
# Before
def test_document_service():
    session_factory = build_session_factory(test_dsn)
    uow = SqlAlchemyUnitOfWork(session_factory)

# After - more flexible
async def test_document_service():
    config = DatabaseProviderConfig(
        name="test",
        provider="sqlite_memory",
        dsn="sqlite:///:memory:"
    )
    provider = DatabaseFactory.create_provider(config.to_database_config())
    await provider.initialize()

    uow = SqlAlchemyUnitOfWork.from_provider(provider)
```

### Integration Tests

Add performance testing to integration tests:

```python
async def test_performance_comparison():
    # Test both providers
    providers = [primary_provider, alternative_provider]

    benchmark_suite = BenchmarkSuite(providers)
    results = await benchmark_suite.run_all_tests()

    # Assert performance requirements
    for result in results:
        assert result.success_rate > 95.0
        assert result.avg_time < 100.0  # 100ms threshold
```

## Common Migration Issues

### Issue 1: Import Errors

**Problem**: New imports not found
**Solution**: Ensure you're importing from the correct modules

```python
# Correct imports
from db.providers.base import IDatabaseProvider
from app.enhanced_container import EnhancedContainer
```

### Issue 2: Session Type Mismatches

**Problem**: Type checking issues with sessions
**Solution**: Use the abstract UoW interface

```python
# Use interface instead of concrete type
from interfaces_adaptor.ports import IUnitOfWork

def my_function(uow: IUnitOfWork):  # Instead of SqlAlchemyUnitOfWork
    # Function works with any UoW implementation
    pass
```

### Issue 3: Configuration Complexity

**Problem**: Complex configuration setup
**Solution**: Start with legacy wrapper

```python
# Simplest approach
config = DatabaseManagerConfig.create_from_legacy_settings(
    pg_async_dsn=existing_dsn,
    vector_dsn=existing_vector_dsn
)
```

## Best Practices for Migration

### 1. Start Small

- Begin with legacy wrapper
- Add one alternative provider
- Test thoroughly before expanding

### 2. Maintain Compatibility

- Keep existing environment variables
- Don't break existing tests
- Provide fallback options

### 3. Gradual Testing

- Test new providers in development first
- Use feature flags for production rollout
- Monitor performance metrics

### 4. Documentation

- Document provider configurations
- Update deployment procedures
- Train team on new capabilities

## Rollback Strategy

If you need to rollback:

### 1. Code Rollback

```python
# Simply switch back to legacy imports
from app.container import Container  # Instead of EnhancedContainer
```

### 2. Configuration Rollback

```python
# Use original configuration
container = Container(orm_async_dsn, vector_dsn)
```

### 3. Environment Rollback

```bash
# Remove new environment variables if needed
unset ALTERNATIVE_DB_DSN
unset ENABLE_PERFORMANCE_TESTING
```

## Getting Help

If you encounter issues during migration:

1. Check the logs for detailed error messages
2. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
3. Verify database connectivity with the example script
4. Test with minimal configuration first

For questions about specific use cases, refer to the [Database Decoupling Guide](database-decoupling.md) or create an issue in the project repository.
