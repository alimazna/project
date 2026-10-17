"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import auth, health, market, plans  # noqa: F401

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router)
api_router.include_router(plans.router)
api_router.include_router(auth.router)
