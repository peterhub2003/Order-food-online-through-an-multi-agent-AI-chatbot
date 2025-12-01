from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib

from ..auth import create_access_token
from ..db import get_db
from ..models.user import User


router = APIRouter(tags=["auth"])


def _hash_password(password: str) -> str:


    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(plain_password: str, hashed_password: str) -> bool:


    return _hash_password(plain_password) == hashed_password


class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/login")
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/register")
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = _hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}



