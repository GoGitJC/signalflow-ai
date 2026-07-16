from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_admin
from app.db.session import get_db
from app.models import AuthAuditEvent, IntegrationAuditEvent
from app.schemas.product import AuditEventRead

router = APIRouter(tags=["audit"])


@router.get("/api/businesses/{business_id}/audit-events", response_model=list[AuditEventRead])
def list_audit_events(
    business_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, description="Search action, status, detail, provider"),
    source: str | None = Query(default=None, description="auth | integration"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_admin),
):
    assert_tenant_access(tenant_id, business_id)
    fetch_limit = min(max(limit * 4, limit), 500)
    integration = list(
        db.scalars(
            select(IntegrationAuditEvent)
            .where(IntegrationAuditEvent.business_id == business_id)
            .order_by(desc(IntegrationAuditEvent.created_at))
            .limit(fetch_limit)
        )
    )
    auth = list(
        db.scalars(
            select(AuthAuditEvent)
            .where(AuthAuditEvent.business_id == business_id)
            .order_by(desc(AuthAuditEvent.created_at))
            .limit(fetch_limit)
        )
    )
    events: list[AuditEventRead] = [
        AuditEventRead(
            id=item.id,
            source="integration",
            business_id=item.business_id,
            provider=item.provider,
            action=item.action,
            status=item.status,
            detail=item.detail,
            created_at=item.created_at,
        )
        for item in integration
    ]
    events.extend(
        AuditEventRead(
            id=item.id,
            source="auth",
            business_id=item.business_id,
            user_id=item.user_id,
            action=item.action,
            status=item.status,
            detail=item.detail,
            created_at=item.created_at,
        )
        for item in auth
    )
    if source in {"auth", "integration"}:
        events = [event for event in events if event.source == source]
    if q:
        needle = q.strip().lower()
        events = [
            event
            for event in events
            if needle
            in " ".join(
                [
                    event.action or "",
                    event.status or "",
                    event.detail or "",
                    event.provider or "",
                    event.source or "",
                ]
            ).lower()
        ]
    events.sort(key=lambda item: item.created_at, reverse=True)
    return events[:limit]
