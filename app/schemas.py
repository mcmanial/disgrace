from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    name: str


class RoomCreate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
