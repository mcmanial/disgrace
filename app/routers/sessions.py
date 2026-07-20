import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.auth import get_current_user
from app.schemas import AvatarUpdate, LoginCreate, PasswordChange, RegisterCreate, UserOut

router = APIRouter(prefix="/api/session", tags=["session"])


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterCreate, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(name=payload.name, password_hash=_hash(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    request.session["user_id"] = user.id
    return user


@router.post("/login", response_model=UserOut)
async def login(payload: LoginCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.name == payload.name))
    if not user or not _verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session["user_id"] = user.id
    return user


@router.patch("/password", status_code=204)
async def change_password(
    payload: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _verify(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if _verify(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=422, detail="New password must be different from current password")
    current_user.password_hash = _hash(payload.new_password)
    db.add(current_user)
    await db.commit()
    return Response(status_code=204)


@router.patch("/avatar", response_model=UserOut)
async def update_avatar(
    payload: AvatarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.avatar_url = payload.avatar_url
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("", status_code=204)
async def delete_session(request: Request):
    request.session.clear()
    return Response(status_code=204)
