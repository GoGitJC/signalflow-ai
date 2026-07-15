class ProviderError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class ProviderAuthError(ProviderError):
    def __init__(self, message: str = "Provider authentication failed"):
        super().__init__(message, status_code=401)


class ProviderNotFoundError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ProviderConflictError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ProviderRateLimitError(ProviderError):
    def __init__(self, message: str = "Provider rate limit exceeded"):
        super().__init__(message, status_code=429, retryable=True)


class ProviderTimeoutError(ProviderError):
    def __init__(self, message: str = "Provider request timed out"):
        super().__init__(message, status_code=504, retryable=True)


class ProviderValidationError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
