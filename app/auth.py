from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="unauthenticated")

    user = await db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="unauthenticated")

    return user


async def get_current_user_ws(session: dict, db: AsyncSession) -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return await db.scalar(select(User).where(User.id == user_id))
