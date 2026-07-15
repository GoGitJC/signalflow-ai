from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.errors import ProviderError
from app.integrations.factory import get_calcom_client, get_retell_client, get_scheduling_provider
from app.models import Integration, IntegrationProvider, VoiceAgent
from app.services.audit import record_audit
from app.services.credentials import decrypt_credentials, encrypt_credentials, mask_secret


def _integration_row(db: Session, business_id: str, provider: IntegrationProvider) -> Integration | None:
    return db.scalar(
        select(Integration).where(
            Integration.business_id == business_id,
            Integration.provider == provider,
        )
    )


def load_retell_credentials(db: Session, business_id: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    row = _integration_row(db, business_id, IntegrationProvider.retell)
    if row:
        creds = decrypt_credentials(row.encrypted_credentials)
        return {
            "api_key": creds.get("api_key", ""),
            "agent_id": creds.get("agent_id") or row.metadata_json.get("agent_id"),
            "agent_name": creds.get("agent_name")
            or row.metadata_json.get("agent_name")
            or settings.retell_agent_name,
            "webhook_secret": creds.get("webhook_secret", ""),
        }
    return {
        "api_key": settings.retell_api_key,
        "agent_id": settings.retell_agent_id or None,
        "agent_name": settings.retell_agent_name,
        "webhook_secret": settings.retell_webhook_secret,
    }


def load_calcom_credentials(db: Session, business_id: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    row = _integration_row(db, business_id, IntegrationProvider.calcom)
    if row:
        creds = decrypt_credentials(row.encrypted_credentials)
        return {
            "api_key": creds.get("api_key", ""),
            "event_type_id": creds.get("event_type_id") or row.metadata_json.get("event_type_id"),
            "event_type_slug": creds.get("event_type_slug") or row.metadata_json.get("event_type_slug"),
            "username": creds.get("username") or row.metadata_json.get("username"),
        }
    return {
        "api_key": settings.calcom_api_key,
        "event_type_id": settings.calcom_event_type_id or None,
        "event_type_slug": settings.calcom_event_type_slug or None,
        "username": settings.calcom_username or None,
    }


def upsert_integration(
    db: Session,
    *,
    business_id: str,
    provider: IntegrationProvider,
    credentials: dict[str, Any],
    metadata: dict[str, Any],
) -> Integration:
    row = _integration_row(db, business_id, provider)
    encrypted = encrypt_credentials(credentials)
    if row is None:
        row = Integration(
            business_id=business_id,
            provider=provider,
            encrypted_credentials=encrypted,
            metadata_json=metadata,
        )
        db.add(row)
        action = "integration_connected"
    else:
        row.encrypted_credentials = encrypted
        row.metadata_json = {**row.metadata_json, **metadata}
        action = "integration_updated"
    record_audit(db, business_id=business_id, provider=provider.value, action=action, status="ok")
    db.flush()
    return row


def retell_status_view(db: Session, business_id: str) -> dict[str, Any]:
    settings = get_settings()
    row = _integration_row(db, business_id, IntegrationProvider.retell)
    creds = load_retell_credentials(db, business_id, settings)
    agent = db.scalar(
        select(VoiceAgent).where(
            VoiceAgent.business_id == business_id,
            VoiceAgent.active.is_(True),
        )
    )
    agent_id = (row.metadata_json.get("agent_id") if row else None) or creds.get("agent_id") or (
        agent.retell_agent_id if agent else None
    )
    return {
        "connected": bool(creds.get("api_key")),
        "mode": settings.integration_mode,
        "agent_name": creds.get("agent_name"),
        "agent_id_masked": mask_secret(agent_id),
        "webhook_url": settings.retell_webhook_url,
        "webhook_configured": bool((row.metadata_json.get("webhook_url") if row else None) or settings.retell_webhook_base_url),
        "last_test_at": row.last_test_at if row else None,
        "last_test_status": row.last_test_status if row else None,
        "last_test_error": row.last_test_error if row else None,
    }


def calcom_status_view(db: Session, business_id: str) -> dict[str, Any]:
    settings = get_settings()
    row = _integration_row(db, business_id, IntegrationProvider.calcom)
    creds = load_calcom_credentials(db, business_id, settings)
    metadata = row.metadata_json if row else {}
    return {
        "connected": bool(creds.get("api_key")),
        "mode": settings.integration_mode,
        "event_type_name": metadata.get("event_type_name"),
        "event_type_id": metadata.get("event_type_id") or creds.get("event_type_id"),
        "event_type_slug": metadata.get("event_type_slug") or creds.get("event_type_slug"),
        "username": metadata.get("username") or creds.get("username"),
        "last_test_at": row.last_test_at if row else None,
        "last_test_status": row.last_test_status if row else None,
        "last_test_error": row.last_test_error if row else None,
    }


def test_retell_connection(db: Session, business_id: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.mock_external_services:
        creds = load_retell_credentials(db, business_id, settings)
        result = {
            "ok": True,
            "agent_id": creds.get("agent_id") or "mock-agent-id",
            "agent_name": creds.get("agent_name"),
            "webhook_url": settings.retell_webhook_url,
            "mocked": True,
        }
        record_audit(
            db,
            business_id=business_id,
            provider="retell",
            action="connection_test",
            status="ok",
            detail="mock",
        )
        return result

    settings.require_live_retell_config()
    creds = load_retell_credentials(db, business_id, settings)
    client = get_retell_client(api_key=creds["api_key"], settings=settings)
    try:
        result = client.test_connection(
            agent_id=creds.get("agent_id"),
            agent_name=creds.get("agent_name") or settings.retell_agent_name,
        )
    except ProviderError as exc:
        record_audit(
            db,
            business_id=business_id,
            provider="retell",
            action="connection_test",
            status="error",
            detail=str(exc),
        )
        raise

    row = upsert_integration(
        db,
        business_id=business_id,
        provider=IntegrationProvider.retell,
        credentials={"api_key": creds["api_key"], "agent_id": result["agent_id"], "agent_name": result["agent_name"]},
        metadata={
            "agent_id": result["agent_id"],
            "agent_name": result["agent_name"],
            "webhook_url": result.get("webhook_url"),
        },
    )
    row.last_test_at = datetime.now(UTC)
    row.last_test_status = "ok"
    row.last_test_error = None

    voice_agent = db.scalar(
        select(VoiceAgent).where(
            VoiceAgent.business_id == business_id,
            VoiceAgent.retell_agent_id == result["agent_id"],
        )
    )
    if voice_agent is None:
        db.add(
            VoiceAgent(
                business_id=business_id,
                retell_agent_id=result["agent_id"],
                retell_agent_name=result["agent_name"],
                name=result["agent_name"],
                greeting="Hello, thanks for calling.",
                system_prompt="You are a helpful receptionist.",
            )
        )
    else:
        voice_agent.retell_agent_name = result["agent_name"]
        voice_agent.name = result["agent_name"]

    record_audit(
        db,
        business_id=business_id,
        provider="retell",
        action="connection_test",
        status="ok",
    )
    db.commit()
    return {**result, "mocked": False}


def test_calcom_connection(db: Session, business_id: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.mock_external_services:
        creds = load_calcom_credentials(db, business_id, settings)
        result = {
            "ok": True,
            "event_type_id": creds.get("event_type_id") or "mock-event-type",
            "slug": creds.get("event_type_slug") or "mock-slug",
            "title": "Mock Event Type",
            "username": creds.get("username"),
            "mocked": True,
        }
        record_audit(
            db,
            business_id=business_id,
            provider="calcom",
            action="connection_test",
            status="ok",
            detail="mock",
        )
        return result

    settings.require_live_calcom_config()
    creds = load_calcom_credentials(db, business_id, settings)
    client = get_calcom_client(
        api_key=creds["api_key"],
        settings=settings,
        event_type_id=creds.get("event_type_id"),
        event_type_slug=creds.get("event_type_slug"),
        username=creds.get("username"),
    )
    try:
        result = client.test_connection()
    except ProviderError as exc:
        record_audit(
            db,
            business_id=business_id,
            provider="calcom",
            action="connection_test",
            status="error",
            detail=str(exc),
        )
        raise

    row = upsert_integration(
        db,
        business_id=business_id,
        provider=IntegrationProvider.calcom,
        credentials={
            "api_key": creds["api_key"],
            "event_type_id": result.get("event_type_id"),
            "event_type_slug": result.get("slug"),
            "username": result.get("username"),
        },
        metadata={
            "event_type_id": result.get("event_type_id"),
            "event_type_slug": result.get("slug"),
            "event_type_name": result.get("title"),
            "username": result.get("username"),
        },
    )
    row.last_test_at = datetime.now(UTC)
    row.last_test_status = "ok"
    row.last_test_error = None
    record_audit(
        db,
        business_id=business_id,
        provider="calcom",
        action="connection_test",
        status="ok",
    )
    db.commit()
    return {**result, "mocked": False}


def resolve_business_for_retell_agent(db: Session, retell_agent_id: str) -> str:
    agent = db.scalar(select(VoiceAgent).where(VoiceAgent.retell_agent_id == retell_agent_id))
    if agent is None:
        raise ValueError(f"No business mapped to Retell agent {retell_agent_id}")
    return agent.business_id


def get_scheduling_for_business(db: Session, business_id: str):
    settings = get_settings()
    creds = load_calcom_credentials(db, business_id, settings)
    return get_scheduling_provider(
        api_key=creds.get("api_key"),
        settings=settings,
        event_type_id=creds.get("event_type_id"),
        event_type_slug=creds.get("event_type_slug"),
        username=creds.get("username"),
    )
