class FPTLLMError(Exception):
    """Base exception for FPT LLM client."""


class AuthenticationError(FPTLLMError):
    pass


class RateLimitError(FPTLLMError):
    def __init__(self, message, status_code=429, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class APIError(FPTLLMError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code
