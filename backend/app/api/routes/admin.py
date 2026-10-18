"""Super-admin routes: plan CRUD with audit trail.

Only ``super_admin`` can mutate plans; ``admin``/``super_admin`` can list.
Every mutation appends a ``PlanVersion`` row recording who changed what.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_super_admin
from app.db.session import get_db
from app.models import Plan, PlanVersion, User

router = APIRouter(prefix="/admin/plans", tags=["admin"])


class PlanPayload(BaseModel):
    code: str = Field(default=None, min_length=1, max_length=50)
    name: str = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    display_price: str | None = None
    billing_interval: str | None = None
    currency: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    is_archived: bool | None = None
    features: list[str] | None = None
    quotas: dict | None = None


def _snapshot(p: Plan) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "description": p.description,
        "display_price": p.display_price,
        "billing_interval": p.billing_interval,
        "currency": p.currency,
        "sort_order": p.sort_order,
        "is_active": p.is_active,
        "is_archived": p.is_archived,
        "features": p.features or [],
        "quotas": p.quotas or {},
        "version": p.version,
    }


def _audit(db: Session, plan: Plan, user: User) -> None:
    db.add(
        PlanVersion(
            plan_id=plan.id,
            name=plan.name,
            display_price=plan.display_price,
            quotas=plan.quotas or {},
            changed_by=user.id,
        )
    )
    plan.version += 1


@router.get("")
def list_admin_plans(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    plans = db.execute(
        select(Plan).order_by(Plan.sort_order, Plan.code)
    ).scalars().all()
    return {"items": [_snapshot(p) for p in plans], "total": len(plans)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_admin_plan(
    payload: PlanPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    if not payload.code or not payload.name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "code and name are required")
    existing = db.execute(select(Plan).where(Plan.code == payload.code)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Plan code '{payload.code}' already exists")
    plan = Plan(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        display_price=payload.display_price or "Free",
        billing_interval=payload.billing_interval or "none",
        currency=payload.currency or "USD",
        sort_order=payload.sort_order or 0,
        is_active=payload.is_active is not False,
        is_archived=bool(payload.is_archived),
        features=payload.features or [],
        quotas=payload.quotas or {},
    )
    db.add(plan)
    db.flush()
    _audit(db, plan, user)
    db.commit()
    db.refresh(plan)
    return {"item": _snapshot(plan)}


@router.put("/{plan_id}")
def update_admin_plan(
    plan_id: int,
    payload: PlanPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    _audit(db, plan, user)
    db.commit()
    db.refresh(plan)
    return {"item": _snapshot(plan)}


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_admin_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    plan.is_archived = True
    plan.is_active = False
    _audit(db, plan, user)
    db.commit()


@router.get("/{plan_id}/versions")
def list_plan_versions(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    rows = db.execute(
        select(PlanVersion).where(PlanVersion.plan_id == plan_id).order_by(PlanVersion.id.desc())
    ).scalars().all()
    return {
        "versions": [
            {
                "id": v.id,
                "name": v.name,
                "display_price": v.display_price,
                "quotas": v.quotas,
                "changed_by": v.changed_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in rows
        ]
    }
