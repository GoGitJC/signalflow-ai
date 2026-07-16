from sqlalchemy.orm import Session

from app.models import AuthAuditEvent, IntegrationAuditEvent


def record_audit(
    db: Session,
    *,
    business_id: str,
    provider: str,
    action: str,
    status: str,
    detail: str | None = None,
) -> None:
    db.add(
        IntegrationAuditEvent(
            business_id=business_id,
            provider=provider,
            action=action,
            status=status,
            detail=detail,
        )
    )
    db.flush()


def record_auth_audit(
    db: Session,
    *,
    action: str,
    status: str,
    business_id: str | None = None,
    user_id: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        AuthAuditEvent(
            business_id=business_id,
            user_id=user_id,
            action=action,
            status=status,
            detail=detail,
        )
    )
    db.flush()
