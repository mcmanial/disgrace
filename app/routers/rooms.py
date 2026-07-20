from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_db
from app.models import Room
from app.schemas import RoomCreate, RoomOut

router = APIRouter(prefix="/api/rooms", tags=["rooms"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[RoomOut])
async def list_rooms(db: AsyncSession = Depends(get_db)):
    result = await db.scalars(select(Room).order_by(Room.id))
    return list(result)


@router.post("", response_model=RoomOut, status_code=201)
async def create_room(payload: RoomCreate, db: AsyncSession = Depends(get_db)):
    room = Room(name=payload.name)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room
