"""Shared FastAPI dependencies: auth, RBAC, DB access."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    raw_sub = payload.get("sub")
    if not isinstance(raw_sub, str) or not raw_sub.isdigit():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject")
    user = db.get(User, int(raw_sub))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    if not user.is_active or user.is_suspended:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return user


def require_roles(*roles: str):
    def check(user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name for r in user.roles}
        if not user_roles.intersection(set(roles)):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return check


require_admin = require_roles("admin", "super_admin")
require_super_admin = require_roles("super_admin")
