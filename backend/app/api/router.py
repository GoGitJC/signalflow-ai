from fastapi import APIRouter

from app.api.routes import (
    appointments,
    auth,
    businesses,
    calls,
    health,
    integrations,
    knowledge_base,
    retell_tools,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(businesses.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(calls.router)
api_router.include_router(appointments.router)
api_router.include_router(integrations.router)
api_router.include_router(retell_tools.router)
api_router.include_router(webhooks.router)
