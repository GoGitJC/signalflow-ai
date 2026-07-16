from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_tenant_access, require_business_member
from app.db.session import get_db
from app.models import Business, VoiceAgent
from app.schemas.voice_agent import VoiceAgentRead, VoiceAgentUpdate

router = APIRouter(tags=["voice-agents"])


@router.get("/api/businesses/{business_id}/voice-agents", response_model=list[VoiceAgentRead])
def list_voice_agents(
    business_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    assert_tenant_access(tenant_id, business_id)
    if not db.get(Business, business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return list(db.scalars(select(VoiceAgent).where(VoiceAgent.business_id == business_id)))


@router.get("/api/voice-agents/{agent_id}", response_model=VoiceAgentRead)
def get_voice_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    agent = db.get(VoiceAgent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Voice agent not found")
    assert_tenant_access(tenant_id, agent.business_id)
    return agent


@router.patch("/api/voice-agents/{agent_id}", response_model=VoiceAgentRead)
def update_voice_agent(
    agent_id: str,
    payload: VoiceAgentUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_business_member),
):
    agent = db.get(VoiceAgent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Voice agent not found")
    assert_tenant_access(tenant_id, agent.business_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    agent.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(agent)
    return agent
