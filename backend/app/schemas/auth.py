"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None = None
    roles: list[str] = []
    is_active: bool = True
    is_suspended: bool = False

    model_config = {"from_attributes": True}

    @field_validator("roles", mode="before")
    @classmethod
    def _roles_to_names(cls, v):
        if isinstance(v, list):
            return [r.name if hasattr(r, "name") else r for r in v]
        return v
