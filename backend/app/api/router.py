from fastapi import APIRouter

from app.api.routes import (
    analytics,
    appointments,
    audit,
    auth,
    businesses,
    callers,
    calls,
    health,
    integrations,
    knowledge_base,
    retell_tools,
    voice_agents,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(businesses.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(calls.router)
api_router.include_router(callers.router)
api_router.include_router(appointments.router)
api_router.include_router(voice_agents.router)
api_router.include_router(analytics.router)
api_router.include_router(audit.router)
api_router.include_router(integrations.router)
api_router.include_router(retell_tools.router)
api_router.include_router(webhooks.router)
