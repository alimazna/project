"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import (
    alerts,
    analysis,
    auth,
    health,
    market,
    plans,
    watchlists,
)  # noqa: F401

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router)
api_router.include_router(plans.router)
api_router.include_router(auth.router)
api_router.include_router(analysis.router)
api_router.include_router(watchlists.router)
api_router.include_router(alerts.router)
