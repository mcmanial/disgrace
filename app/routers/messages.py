from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.db import get_db
from app.models import Message, Reaction, User
from app.schemas import MessageEdit, MessageOut, ReactionOut, ReactionToggle, ReplySnippet

router = APIRouter(prefix="/api/rooms", tags=["messages"], dependencies=[Depends(get_current_user)])
search_router = APIRouter(prefix="/api/messages", tags=["search"], dependencies=[Depends(get_current_user)])


def _serialize(m: Message) -> MessageOut:
    reply_to = None
    if m.reply_to_id is not None:
        # reply_to_msg is eagerly loaded as m.reply_msg via selectinload
        rm = getattr(m, "reply_msg", None)
        if rm:
            reply_to = ReplySnippet(
                id=rm.id,
                user_name=rm.user.name if rm.user else None,
                body=rm.body,
            )

    reactions = [
        ReactionOut(
            emoji=r.emoji,
            user_id=r.user_id,
            user_name=r.user.name if r.user else None,
        )
        for r in (m.reactions or [])
    ]

    return MessageOut(
        id=m.id,
        room_id=m.room_id,
        user_id=m.user_id,
        user_name=m.user.name if m.user else None,
        user_avatar=m.user.avatar_url if m.user else None,
        reply_to=reply_to,
        body=m.body,
        edited_at=m.edited_at,
        created_at=m.created_at,
        reactions=reactions,
    )


def _query_options():
    return [
        selectinload(Message.user),
        selectinload(Message.reactions).selectinload(Reaction.user),
        selectinload(Message.reply_msg).selectinload(Message.user),
    ]


@router.get("/{room_id}/messages", response_model=list[MessageOut])
async def list_messages(
    room_id: int,
    limit: int = 50,
    before_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Message)
        .where(Message.room_id == room_id)
        .options(*_query_options())
    )
    if before_id is not None:
        query = query.where(Message.id < before_id)
    query = query.order_by(Message.id.desc()).limit(limit)
    result = await db.scalars(query)
    return [_serialize(m) for m in reversed(result.all())]


@router.patch("/{room_id}/messages/{message_id}", response_model=MessageOut)
async def edit_message(
    room_id: int,
    message_id: int,
    payload: MessageEdit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = await db.scalar(
        select(Message).where(Message.id == message_id, Message.room_id == room_id).options(*_query_options())
    )
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's message")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message body cannot be empty")
    msg.body = body
    msg.edited_at = datetime.utcnow()
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    # reload with relationships after refresh
    msg = await db.scalar(
        select(Message).where(Message.id == message_id).options(*_query_options())
    )
    return _serialize(msg)


@router.delete("/{room_id}/messages/{message_id}", status_code=204)
async def delete_message(
    room_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = await db.scalar(select(Message).where(Message.id == message_id, Message.room_id == room_id))
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")
    await db.delete(msg)
    await db.commit()


@router.post("/{room_id}/messages/{message_id}/react", response_model=MessageOut)
async def toggle_reaction(
    room_id: int,
    message_id: int,
    payload: ReactionToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = await db.scalar(
        select(Message).where(Message.id == message_id, Message.room_id == room_id)
    )
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")

    existing = await db.scalar(
        select(Reaction).where(
            Reaction.message_id == message_id,
            Reaction.user_id == current_user.id,
            Reaction.emoji == payload.emoji,
        )
    )
    if existing:
        await db.delete(existing)
    else:
        db.add(Reaction(message_id=message_id, user_id=current_user.id, emoji=payload.emoji))
    await db.commit()

    msg = await db.scalar(
        select(Message).where(Message.id == message_id).options(*_query_options())
    )
    return _serialize(msg)


@search_router.get("/search", response_model=list[MessageOut])
async def search_messages(
    q: str | None = None,
    from_user: str | None = None,
    in_channel: int | None = None,
    has: str | None = None,
    mentions: str | None = None,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    query = select(Message).options(*_query_options())

    if q:
        query = query.where(Message.body.ilike(f"%{q}%"))
    if in_channel:
        query = query.where(Message.room_id == in_channel)
    if from_user:
        query = query.join(Message.user).where(User.name.ilike(f"%{from_user}%"))
    if has == "link":
        query = query.where(or_(
            Message.body.ilike("%http://%"),
            Message.body.ilike("%https://%"),
        ))
    if mentions:
        query = query.where(Message.body.ilike(f"%@{mentions}%"))

    query = query.order_by(Message.id.desc()).limit(limit)
    result = await db.scalars(query)
    return [_serialize(m) for m in result.all()]
