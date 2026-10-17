"""Public plans endpoint — database-driven pricing (ADR-010)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Plan

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("")
def list_public_plans(db: Session = Depends(get_db)):
    plans = db.execute(
        select(Plan).where(Plan.is_active.is_(True), Plan.is_archived.is_(False))
        .order_by(Plan.sort_order)
    ).scalars().all()
    return {
        "items": [
            {
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "display_price": p.display_price,
                "billing_interval": p.billing_interval,
                "currency": p.currency,
                "features": p.features or [],
                "quotas": p.quotas or {},
            }
            for p in plans
        ],
        "total": len(plans),
    }
