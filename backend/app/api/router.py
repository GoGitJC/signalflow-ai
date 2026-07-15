from fastapi import APIRouter

from app.api.routes import (
    appointments,
    businesses,
    calls,
    health,
    integrations,
    knowledge_base,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(businesses.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(calls.router)
api_router.include_router(appointments.router)
api_router.include_router(integrations.router)
api_router.include_router(webhooks.router)
