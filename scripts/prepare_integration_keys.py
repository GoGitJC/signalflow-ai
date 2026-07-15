#!/usr/bin/env python3
"""Prepare local non-secret integration persistence keys in .env (never prints secrets)."""

from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Install cryptography in the backend container, or run via docker compose.", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def upsert(text: str, key: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    line = f"{key}={value}"
    if pattern.search(text):
        current = None
        for row in text.splitlines():
            if row.startswith(f"{key}="):
                current = row.split("=", 1)[1].strip().strip('"').strip("'")
                break
        if current:
            return text, False
        return pattern.sub(line, text, count=1), True
    if not text.endswith("\n"):
        text += "\n"
    return text + line + "\n", True


def main() -> int:
    if not ENV_PATH.exists():
        print("error: .env not found", file=sys.stderr)
        return 1
    text = ENV_PATH.read_text()
    changed: list[str] = []
    text, did = upsert(text, "SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    if did:
        changed.append("SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY")
    owner = secrets.token_urlsafe(32)
    text, did = upsert(text, "OWNER_API_TOKEN", owner)
    if did:
        changed.append("OWNER_API_TOKEN")
    # Align VITE token with OWNER when empty
    vals = {}
    for row in text.splitlines():
        if "=" in row and not row.strip().startswith("#"):
            k, _, v = row.partition("=")
            vals[k.strip()] = v.strip()
    owner_val = vals.get("OWNER_API_TOKEN", "")
    vite = vals.get("VITE_OWNER_API_TOKEN", "")
    if owner_val and not vite:
        text, did = upsert(text, "VITE_OWNER_API_TOKEN", owner_val)
        if did:
            changed.append("VITE_OWNER_API_TOKEN")
    text, did = upsert(text, "ALLOW_LIVE_BOOKING", "false")
    if did:
        changed.append("ALLOW_LIVE_BOOKING")
    text, did = upsert(text, "CALCOM_EVENT_TYPES_API_VERSION", "2024-06-14")
    if did:
        changed.append("CALCOM_EVENT_TYPES_API_VERSION")
    ENV_PATH.write_text(text)
    print(json_dumps_safe(changed))
    return 0


def json_dumps_safe(changed: list[str]) -> str:
    import json

    return json.dumps({"updated_keys": changed, "env": ".env", "committed": False})


if __name__ == "__main__":
    raise SystemExit(main())
