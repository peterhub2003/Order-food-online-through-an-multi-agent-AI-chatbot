from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreateIn(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class UserUpdateIn(BaseModel):
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
