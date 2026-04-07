import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.chat.models import Conversation, Message
from app.listings.models import Listing


async def get_or_create_conversation(
    db: AsyncSession,
    listing_id: uuid.UUID,
    buyer_id: uuid.UUID,
) -> Conversation:
    # Нельзя начать чат с самим собой
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if listing.owner_id == buyer_id:
        raise HTTPException(status_code=400, detail="Нельзя начать чат с самим собой")

    existing = await db.execute(
        select(Conversation).where(
            Conversation.listing_id == listing_id,
            Conversation.buyer_id == buyer_id,
        )
    )
    conv = existing.scalar_one_or_none()
    if conv:
        return conv

    conv = Conversation(
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=listing.owner_id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def get_my_conversations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation).where(
            (Conversation.buyer_id == user_id) | (Conversation.seller_id == user_id)
        ).order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()

    if not conversations:
        return []

    # Собираем все ID собеседников за один запрос
    other_ids = [
        conv.seller_id if conv.buyer_id == user_id else conv.buyer_id
        for conv in conversations
    ]
    users_result = await db.execute(
        select(User).where(User.id.in_(other_ids))
    )
    users_by_id = {u.id: u for u in users_result.scalars().all()}

    enriched = []
    for conv in conversations:
        other_id = conv.seller_id if conv.buyer_id == user_id else conv.buyer_id
        conv._other_user = users_by_id.get(other_id)

        last = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        conv._last_message = last.scalar_one_or_none()

        unread_result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conv.id,
                Message.sender_id != user_id,
                Message.is_read == False,  # noqa: E712
            )
        )
        conv._unread_count = unread_result.scalar_one()

        enriched.append(conv)
    return enriched


async def get_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
    before_id: Optional[uuid.UUID] = None,
) -> list[Message]:
    conv = await _get_conversation_for_member(db, conversation_id, user_id)

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    if before_id:
        pivot = await db.execute(select(Message).where(Message.id == before_id))
        pivot_msg = pivot.scalar_one_or_none()
        if pivot_msg:
            query = query.where(Message.created_at < pivot_msg.created_at)

    result = await db.execute(query)
    return list(reversed(result.scalars().all()))


async def mark_read(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await _get_conversation_for_member(db, conversation_id, user_id)
    await db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()


async def save_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    sender_id: uuid.UUID,
    text: str,
) -> Message:
    msg = Message(conversation_id=conversation_id, sender_id=sender_id, text=text)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_notification_data(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    sender_id: uuid.UUID,
) -> tuple[Optional[str], str]:
    """Возвращает (email получателя, имя отправителя) для email-уведомления."""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        return None, ""

    recipient_id = conv.seller_id if conv.buyer_id == sender_id else conv.buyer_id

    users_result = await db.execute(
        select(User).where(User.id.in_([sender_id, recipient_id]))
    )
    users = {u.id: u for u in users_result.scalars().all()}

    recipient = users.get(recipient_id)
    sender = users.get(sender_id)

    if not recipient or not sender:
        return None, ""

    return recipient.email, sender.full_name or sender.email


async def _get_conversation_for_member(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if conv.buyer_id != user_id and conv.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому чату")
    return conv
