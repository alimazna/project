"""TrendCipher backend application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  (register models)
from app.core.config import settings
from app.db.session import Base, engine, init_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Explainable cryptocurrency market-intelligence API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
def healthz():
    return {"status": "ok", "app": settings.app_name, "version": "0.1.0"}


@app.get("/", tags=["system"])
def root():
    return {"service": settings.app_name, "docs": "/docs"}


# API routers are registered in app/api/router.py
from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix=settings.api_prefix)
