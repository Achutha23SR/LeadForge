from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from lib.auth import create_token, get_current_user, hash_password, public_user, verify_password
from lib.db import db
from models.leadforge import AuthRequest, AuthResponse, RegisterRequest
import uuid
from datetime import datetime, timezone


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, response: Response):
    email = payload.email.strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = {
        "id": str(uuid.uuid4()), "email": email, "full_name": payload.full_name.strip(),
        "password_hash": hash_password(payload.password), "role": "USER", "credits": 1000,
        "credit_used": 0, "disabled": False, "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    response.set_cookie("lf_session", create_token(user), httponly=True, samesite="lax", max_age=43200)
    return AuthResponse(user=public_user(user), message="Account created")


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthRequest, response: Response):
    user = await db.users.find_one({"email": payload.email.strip().lower()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("disabled"):
        raise HTTPException(status_code=403, detail="This account is disabled")
    response.set_cookie("lf_session", create_token(user), httponly=True, samesite="lax", max_age=43200)
    return AuthResponse(user=public_user(user), message="Welcome back")


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("lf_session")
    return {"message": "Signed out"}


@router.get("/me", response_model=AuthResponse)
async def me(lf_session: str | None = Cookie(default=None)):
    if not lf_session:
        return AuthResponse(user=None, message="No active session")
    try:
        user = await get_current_user(lf_session)
    except HTTPException:
        return AuthResponse(user=None, message="No active session")
    return AuthResponse(user=public_user(user), message="Active session")


@router.post("/refresh", response_model=AuthResponse)
async def refresh(response: Response, lf_session: str | None = Cookie(default=None)):
    if not lf_session:
        raise HTTPException(status_code=401, detail="No active session")
    from lib.auth import get_current_user
    user = await get_current_user(lf_session)
    response.set_cookie("lf_session", create_token(user), httponly=True, samesite="lax", max_age=43200)
    return AuthResponse(user=public_user(user), message="Session refreshed")