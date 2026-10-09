import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from passlib.context import CryptContext

from lib.db import db
from models.leadforge import UserPublic


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "leadforge-development-secret")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def public_user(user: dict[str, Any]) -> UserPublic:
    return UserPublic(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user.get("role", "USER"),
        credits=int(user.get("credits", 1000)),
    )


def create_token(user: dict[str, Any]) -> str:
    return jwt.encode(
        {
            "sub": user["id"],
            "role": user.get("role", "USER"),
            "exp": datetime.now(timezone.utc) + timedelta(hours=12),
            "jti": str(uuid.uuid4()),
        },
        JWT_SECRET,
        algorithm="HS256",
    )


async def get_current_user(lf_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    if not lf_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue")
    try:
        payload = jwt.decode(lf_session, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Your session has expired") from exc
    user = await db.users.find_one({"id": user_id})
    if not user or user.get("disabled"):
        raise HTTPException(status_code=401, detail="Account unavailable")
    return user


async def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user