"""User watchlists — authenticated CRUD scoped to the current user.

Uses the existing Watchlist / WatchlistItem models. Every query is scoped by
``user_id`` so cross-user access is impossible (RBAC + isolation, ADR-005).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, Watchlist, WatchlistItem
from app.services.quotas import enforce_quota

router = APIRouter(prefix="/watchlists", tags=["watchlists"])

MAX_ITEMS = 100


class WatchlistCreate(BaseModel):
    name: str = Field(default="Default", max_length=120)
    symbols: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)


class WatchlistUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    symbols: list[str] | None = Field(default=None, max_length=MAX_ITEMS)


def _snapshot(row: Watchlist) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "is_default": row.is_default,
        "symbols": [item.symbol for item in row.items],
    }


def _get_owned(db: Session, user: User, watchlist_id: int) -> Watchlist:
    row = db.get(Watchlist, watchlist_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Watchlist not found")
    return row


@router.get("")
def list_watchlists(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    rows = db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id).order_by(Watchlist.id)
    ).scalars().all()
    return {"watchlists": [_snapshot(r) for r in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    enforce_quota(db, user, "watchlists")
    row = Watchlist(user_id=user.id, name=payload.name, is_default=False)
    db.add(row)
    db.flush()
    for sym in payload.symbols:
        db.add(WatchlistItem(watchlist_id=row.id, symbol=sym.upper()))
    db.commit()
    db.refresh(row)
    return {"watchlist": _snapshot(row)}


@router.get("/{watchlist_id}")
def get_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return {"watchlist": _snapshot(_get_owned(db, user, watchlist_id))}


@router.put("/{watchlist_id}")
def update_watchlist(
    watchlist_id: int,
    payload: WatchlistUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = _get_owned(db, user, watchlist_id)
    if payload.name is not None and payload.name.strip():
        row.name = payload.name.strip()
    if payload.symbols is not None:
        row.items.clear()
        for sym in payload.symbols:
            row.items.append(WatchlistItem(watchlist_id=row.id, symbol=sym.upper()))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"watchlist": _snapshot(row)}


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = _get_owned(db, user, watchlist_id)
    db.delete(row)
    db.commit()
