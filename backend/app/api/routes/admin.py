"""Super-admin routes: plan CRUD, user management, symbol enable/disable.

Only ``super_admin`` can mutate plans/symbols; ``admin``/``super_admin`` can list.
Every plan mutation appends a ``PlanVersion`` row recording who changed what.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_super_admin
from app.db.session import get_db
from app.models import (
    Alert,
    Plan,
    PlanVersion,
    ProviderHealth,
    Role,
    Subscription,
    Symbol,
    User,
    Watchlist,
)
from app.services.billing import billing_status

plans_router = APIRouter(prefix="/admin/plans", tags=["admin"])
users_router = APIRouter(prefix="/admin/users", tags=["admin"])
system_router = APIRouter(prefix="/admin/system", tags=["admin"])
symbols_router = APIRouter(prefix="/admin/symbols", tags=["admin"])


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


@plans_router.get("")
def list_admin_plans(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    plans = db.execute(
        select(Plan).order_by(Plan.sort_order, Plan.code)
    ).scalars().all()
    return {"items": [_snapshot(p) for p in plans], "total": len(plans)}


@plans_router.post("", status_code=status.HTTP_201_CREATED)
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


@plans_router.put("/{plan_id}")
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


@plans_router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@plans_router.get("/{plan_id}/versions")
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


# ---------------------------------------------------------------- user admin


class UserUpdate(BaseModel):
    is_active: bool | None = None
    is_suspended: bool | None = None
    roles: list[str] | None = None


def _user_out(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "is_active": u.is_active,
        "is_suspended": u.is_suspended,
        "roles": [r.name for r in u.roles],
        "plan": u.plan.code if u.plan else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


@users_router.get("")
def list_admin_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    rows = db.execute(select(User).order_by(User.id)).scalars().all()
    return {"items": [_user_out(u) for u in rows], "total": len(rows)}


@users_router.put("/{user_id}")
def update_admin_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_super_admin),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot modify your own account")
    if payload.is_active is not None:
        target.is_active = payload.is_active
    if payload.is_suspended is not None:
        target.is_suspended = payload.is_suspended
    if payload.roles is not None:
        valid = set(db.execute(select(Role.name)).scalars().all())
        for r in payload.roles:
            if r not in valid:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown role '{r}'")
        target.roles = [db.execute(select(Role).where(Role.name == r)).scalar_one() for r in payload.roles]
    db.commit()
    db.refresh(target)
    return {"item": _user_out(target)}


# ---------------------------------------------------------------- system overview


@system_router.get("")
def admin_system_overview(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """Counts, provider health, and billing configuration for the admin panel."""
    user_count = db.execute(select(User.id)).scalars().all()
    plan_count = db.execute(select(Plan.id)).scalars().all()
    sub_active = db.execute(
        select(Subscription.id).where(Subscription.status == "active")
    ).scalars().all()
    watchlist_count = db.execute(select(Watchlist.id)).scalars().all()
    alert_count = db.execute(select(Alert.id)).scalars().all()
    providers = db.execute(select(ProviderHealth).order_by(ProviderHealth.id)).scalars().all()
    return {
        "counts": {
            "users": len(user_count),
            "plans": len(plan_count),
            "active_subscriptions": len(sub_active),
            "watchlists": len(watchlist_count),
            "alerts": len(alert_count),
        },
        "providers": [
            {
                "provider": p.provider,
                "status": p.status,
                "last_success_at": p.last_success_at.isoformat() if p.last_success_at else None,
                "last_error": p.last_error,
                "error_count": p.error_count,
            }
            for p in providers
        ],
        "billing": billing_status(),
    }


# ---------------------------------------------------------------- symbol enable/disable


class SymbolTogglePayload(BaseModel):
    is_active: bool


def _symbol_out(s: Symbol) -> dict:
    return {
        "symbol": s.symbol,
        "base": s.base,
        "quote": s.quote,
        "display_name": s.display_name,
        "provider": s.provider,
        "is_active": s.is_active,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@symbols_router.get("")
def list_admin_symbols(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    active: bool | None = Query(None, description="Filter by activation state"),
) -> dict:
    """List all known symbols with their activation state (admin/super)."""
    q = select(Symbol).order_by(Symbol.symbol)
    if active is not None:
        q = q.where(Symbol.is_active == active)
    rows = db.execute(q).scalars().all()
    return {"symbols": [_symbol_out(s) for s in rows]}


@symbols_router.put("/{symbol:path}", status_code=status.HTTP_200_OK)
def toggle_symbol(
    symbol: str,
    payload: SymbolTogglePayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
) -> dict:
    """Enable or disable a symbol (super_admin only)."""
    from app.models import utcnow

    row = db.get(Symbol, symbol.upper())
    if row is None:
        raise HTTPException(404, f"Symbol {symbol.upper()} not found")
    row.is_active = payload.is_active
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"item": _symbol_out(row)}


@symbols_router.post("/sync-catalog", status_code=status.HTTP_200_OK)
def sync_symbol_catalog(
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
    tier: int | None = Query(None, ge=1, le=2, description="Only sync a specific tier"),
) -> dict:
    """Insert any catalog symbols missing from DB and return totals."""
    from app.core.symbols import default_symbols

    tiers = {tier} if tier else {1, 2}
    catalog = default_symbols(tiers=tiers)
    added = 0
    for s in catalog:
        existing = db.get(Symbol, s.symbol)
        if existing is None:
            db.add(
                Symbol(
                    symbol=s.symbol,
                    base=s.base,
                    quote=s.quote,
                    display_name=s.display_name,
                    provider="kraken",
                    is_active=True,
                )
            )
            added += 1
    db.commit()
    total = len(db.execute(select(Symbol)).scalars().all())
    return {"catalog_size": len(catalog), "added": added, "db_total": total}
