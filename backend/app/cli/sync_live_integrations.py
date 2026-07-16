"""CLI entrypoint without rewriting host .env from the container."""

from __future__ import annotations

import argparse
import json
import os
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Business, User, UserRole
from app.services.integrations import sync_live_integrations_for_business


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync live integrations onto a business")
    parser.add_argument("--business-id", default=os.environ.get("VITE_BUSINESS_ID") or None)
    args = parser.parse_args()
    settings = get_settings()
    business_id = args.business_id
    if not business_id:
        print("error: --business-id or VITE_BUSINESS_ID is required", file=sys.stderr)
        return 1
    if not settings.credential_encryption_key:
        print(
            "error: SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY is required "
            "(run scripts/prepare_integration_keys.py)",
            file=sys.stderr,
        )
        return 1

    with SessionLocal() as db:
        if db.get(Business, business_id) is None:
            print("error: business not found", file=sys.stderr)
            return 1
        owner = db.scalar(
            select(User).where(
                User.business_id == business_id,
                User.role.in_([UserRole.owner, UserRole.admin]),
            )
        )
        if owner is None:
            db.add(
                User(
                    business_id=business_id,
                    name="Owner",
                    email=f"owner+{business_id[:8]}@signalflow.local",
                    role=UserRole.owner,
                )
            )
            db.commit()
        try:
            result = sync_live_integrations_for_business(db, business_id)
        except Exception as exc:
            print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    print(
        json.dumps(
            {
                "business_id": result["business_id"],
                "retell": result["retell"],
                "calcom": result["calcom"],
                "proposed_webhook_url": settings.retell_webhook_url,
                "tool_urls": {
                    "check_availability": (
                        f"{settings.app_public_api_url.rstrip('/')}/api/retell/tools/check_availability"
                    ),
                    "book_appointment": (
                        f"{settings.app_public_api_url.rstrip('/')}/api/retell/tools/book_appointment"
                    ),
                },
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
