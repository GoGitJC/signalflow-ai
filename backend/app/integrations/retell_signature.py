import hashlib
import hmac
import re
import time

from fastapi import HTTPException, status

_SIGNATURE_PATTERN = re.compile(r"v=(\d+),d=([a-f0-9]+)")


def verify_retell_signature(raw_body: str, signature: str | None, api_key: str) -> None:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retell API key is not configured for webhook verification",
        )
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature"
        )
    match = _SIGNATURE_PATTERN.search(signature)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )
    timestamp, digest = match.group(1), match.group(2)
    now_ms = int(time.time() * 1000)
    if abs(now_ms - int(timestamp)) > 5 * 60 * 1000:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook signature expired"
        )
    expected = hmac.new(
        api_key.encode(),
        (raw_body + timestamp).encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, digest):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )
