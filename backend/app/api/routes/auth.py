"""Authentication endpoints: register, login, refresh, logout, me, bootstrap."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.ratelimit import rate_limit
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models import Role, User
from app.models import Session as SessionModel
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _as_utc(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; normalize everything to aware UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _ensure_roles(db: Session) -> dict[str, Role]:
    roles = {r.name: r for r in db.execute(select(Role)).scalars()}
    for name in ("user", "admin", "super_admin"):
        if name not in roles:
            role = Role(name=name)
            db.add(role)
            roles[name] = role
    db.commit()
    return roles


def _create_session(db: Session, user: User) -> str:
    refresh = generate_refresh_token()
    db.add(
        SessionModel(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_ttl_days),
        )
    )
    db.commit()
    return refresh


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(10, 60, scope="register"))],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    roles = _ensure_roles(db)
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    # First registered user becomes super_admin (secure bootstrap).
    is_first = db.execute(select(User)).first() is None

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    user.roles = [roles["user"]]
    if is_first:
        user.roles.append(roles["super_admin"])
    db.add(user)
    db.commit()
    db.refresh(user)

    refresh = _create_session(db, user)
    access = create_access_token(subject=user.id, extra={"roles": [r.name for r in user.roles]})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(20, 60, scope="login"))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active or user.is_suspended:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    refresh = _create_session(db, user)
    access = create_access_token(subject=user.id, extra={"roles": [r.name for r in user.roles]})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(30, 60, scope="refresh"))],
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    row = db.execute(
        select(SessionModel).where(
            SessionModel.refresh_token_hash == hash_refresh_token(payload.refresh_token)
        )
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if _as_utc(row.expires_at) < datetime.now(UTC):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled")

    # rotate
    row.revoked_at = datetime.now(UTC)
    db.add(row)
    refresh = _create_session(db, user)
    access = create_access_token(subject=user.id, extra={"roles": [r.name for r in user.roles]})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    row = db.execute(
        select(SessionModel).where(
            SessionModel.refresh_token_hash == hash_refresh_token(payload.refresh_token)
        )
    ).scalar_one_or_none()
    if row is not None:
        row.revoked_at = datetime.now(UTC)
        db.add(row)
        db.commit()
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/bootstrap-super-admin", status_code=status.HTTP_201_CREATED)
def bootstrap_super_admin(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Idempotent secure first-run bootstrap: creates the initial super admin.

    Fails with 409 if any super_admin already exists.
    """
    roles = _ensure_roles(db)
    existing_admin = db.execute(select(Role).where(Role.name == "super_admin")).scalar_one_or_none()
    if existing_admin is not None:
        has_admin = db.execute(
            select(User).join(User.roles).where(Role.name == "super_admin")
        ).first()
        if has_admin:
            raise HTTPException(status.HTTP_409_CONFLICT, "Super admin already exists")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    user.roles = [roles["user"], roles["super_admin"]]
    db.add(user)
    db.commit()
    return {"status": "ok", "email": user.email}
