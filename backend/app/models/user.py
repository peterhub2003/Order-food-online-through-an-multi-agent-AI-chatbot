from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from ..db import Base


class User(Base):
    """Application user.

    This is intentionally minimal: you can later plug in a real auth system
    (OAuth2, JWT, etc.). For now it provides a stable identity so that orders
    can be tied to individual users instead of anonymous sessions.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
