from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.metrics import metrics
from app.db.session import SessionLocal
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    """Liveness probe — process is up."""
    return HealthResponse(status="ok", service=get_settings().app_name, timestamp=datetime.now(UTC))


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    """Readiness probe — database reachable."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface readiness failure
        raise HTTPException(
            status_code=503,
            detail={"code": "not_ready", "message": "Database unavailable", "error": str(exc)},
        ) from exc
    return ReadyResponse(
        status="ok",
        service=get_settings().app_name,
        timestamp=datetime.now(UTC),
        checks={"database": "ok"},
    )


@router.get("/metrics")
def prometheus_metrics() -> Response:
    body = metrics.render_prometheus()
    return PlainTextResponse(body or "# no metrics yet\n", media_type="text/plain; version=0.0.4")
