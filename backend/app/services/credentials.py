import json
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status

from app.core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().credential_encryption_key.strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credential encryption key is not configured",
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_credentials(payload: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(payload).encode()).decode()


def decrypt_credentials(blob: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(_fernet().decrypt(blob.encode()).decode()))
    except (InvalidToken, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored credentials could not be decrypted",
        ) from exc


def mask_secret(value: str | None, visible: int = 4) -> str | None:
    if not value:
        return None
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * (len(value) - visible)}{value[-visible:]}"
