from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import SessionCreate, UserOut

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("", response_model=UserOut, status_code=201)
async def create_session(payload: SessionCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user = User(name=payload.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    request.session["user_id"] = user.id
    return user


@router.delete("", status_code=204)
async def delete_session(request: Request):
    request.session.clear()
    return Response(status_code=204)
