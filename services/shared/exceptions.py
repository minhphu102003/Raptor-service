"""
Standardized exceptions for the services module.
Provides consistent error handling patterns across all services.
"""

from typing import Any, Dict, List, Optional, Union


class ServiceError(Exception):
    """Base exception for all service-related errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
        }


class ConfigurationError(ServiceError):
    """Raised when there's a configuration-related error"""

    pass


class ValidationError(ServiceError):
    """Raised when input validation fails"""

    pass


class EmbeddingError(ServiceError):
    """Raised when embedding generation fails"""

    pass


class LLMError(ServiceError):
    """Raised when LLM operations fail"""

    pass


class ClusteringError(ServiceError):
    """Raised when clustering operations fail"""

    pass


class PersistenceError(ServiceError):
    """Raised when database/persistence operations fail"""

    pass


class RaptorBuildError(ServiceError):
    """Raised when RAPTOR tree building fails"""

    pass


class ModelNotSupportedError(ConfigurationError):
    """Raised when an unsupported model is requested"""

    def __init__(self, model_name: str, supported_models: Optional[List[str]] = None):
        context: Dict[str, Any] = {"model_name": model_name}
        if supported_models:
            context["supported_models"] = supported_models

        message = f"Model '{model_name}' is not supported"
        if supported_models:
            message += f". Supported models: {supported_models}"

        super().__init__(message, "MODEL_NOT_SUPPORTED", context)


class EmbeddingDimensionError(EmbeddingError):
    """Raised when embedding dimensions don't match expected values"""

    def __init__(self, expected: int, actual: int, index: Optional[int] = None):
        context = {"expected_dimension": expected, "actual_dimension": actual}
        if index is not None:
            context["vector_index"] = index

        message = f"Embedding dimension mismatch: expected {expected}, got {actual}"
        if index is not None:
            message += f" at index {index}"

        super().__init__(message, "EMBEDDING_DIMENSION_MISMATCH", context)


class ContextLimitExceededError(LLMError):
    """Raised when input + output tokens exceed model context limit"""

    def __init__(self, model: str, input_tokens: int, output_tokens: int, limit: int):
        context = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "context_limit": limit,
            "total_tokens": input_tokens + output_tokens,
        }

        message = (
            f"Context limit exceeded for model '{model}': "
            f"input ({input_tokens}) + output ({output_tokens}) = {input_tokens + output_tokens} > {limit}"
        )

        super().__init__(message, "CONTEXT_LIMIT_EXCEEDED", context)


class ThrottlingError(ServiceError):
    """Raised when rate limiting/throttling prevents operation"""

    def __init__(self, service: str, retry_after: Optional[float] = None):
        context: Dict[str, Any] = {"service": service}
        if retry_after:
            context["retry_after_seconds"] = retry_after

        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(message, "RATE_LIMIT_EXCEEDED", context)


class DataIntegrityError(PersistenceError):
    """Raised when data integrity constraints are violated"""

    def __init__(self, operation: str, entity: str, constraint: str):
        context = {"operation": operation, "entity": entity, "constraint": constraint}

        message = f"Data integrity violation in {operation} for {entity}: {constraint}"
        super().__init__(message, "DATA_INTEGRITY_VIOLATION", context)
