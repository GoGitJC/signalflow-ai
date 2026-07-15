from sqlalchemy.orm import Session

from app.models import IntegrationAuditEvent


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
