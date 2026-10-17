"""System health endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ProviderHealth

router = APIRouter(prefix="/health", tags=["system"])


@router.get("")
def system_health(db: Session = Depends(get_db)):
    providers = db.execute(select(ProviderHealth)).scalars().all()
    return {
        "status": "ok",
        "providers": [
            {
                "provider": p.provider,
                "status": p.status,
                "last_success_at": p.last_success_at,
                "last_error": p.last_error,
                "error_count": p.error_count,
            }
            for p in providers
        ],
    }
