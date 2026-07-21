import time
from typing import Any

import httpx

from app.core.config import Settings
from app.integrations.errors import (
    ProviderAuthError,
    ProviderConflictError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)


def _map_response_error(response: httpx.Response) -> ProviderError:
    status = response.status_code
    try:
        payload = response.json()
        message = payload.get("message") or payload.get("error") or response.text[:200]
    except Exception:
        message = response.text[:200] or f"Upstream error ({status})"
    if status == 401 or status == 403:
        return ProviderAuthError(message)
    if status == 404:
        return ProviderNotFoundError(message)
    if status == 409:
        return ProviderConflictError(message)
    if status in {400, 422}:
        return ProviderValidationError(message)
    if status == 429:
        return ProviderRateLimitError(message)
    if status >= 500:
        return ProviderError(message, status_code=status, retryable=True)
    return ProviderError(message, status_code=status)


def request_json(
    settings: Settings,
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    retryable: bool = False,
) -> Any:
    attempts = 3 if retryable else 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
                response = client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
        except httpx.TimeoutException as exc:
            last_error = ProviderTimeoutError()
            if attempt + 1 < attempts:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise last_error from exc
        except httpx.HTTPError as exc:
            raise ProviderError("Provider network error", retryable=True) from exc

        if response.status_code >= 400:
            mapped = _map_response_error(response)
            if mapped.retryable and attempt + 1 < attempts:
                time.sleep(0.2 * (attempt + 1))
                last_error = mapped
                continue
            raise mapped
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()
    if last_error:
        raise last_error
    raise ProviderError("Provider request failed")
