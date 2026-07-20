from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_db
from app.models import Message
from app.schemas import MessageOut

router = APIRouter(prefix="/api/rooms", tags=["messages"], dependencies=[Depends(get_current_user)])


@router.get("/{room_id}/messages", response_model=list[MessageOut])
async def list_messages(
    room_id: int,
    limit: int = 50,
    before_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Message).where(Message.room_id == room_id)
    if before_id is not None:
        query = query.where(Message.id < before_id)
    query = query.order_by(Message.id.desc()).limit(limit)

    result = await db.scalars(query)
    return list(reversed(result.all()))
