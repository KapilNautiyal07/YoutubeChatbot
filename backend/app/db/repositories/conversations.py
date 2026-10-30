import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, conversation_id: uuid.UUID, with_messages: bool = False) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        if with_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_video(self, video_id: uuid.UUID) -> Sequence[tuple[Conversation, int]]:
        count = (
            select(func.count(Message.id))
            .where(Message.conversation_id == Conversation.id)
            .correlate(Conversation)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Conversation, count)
            .where(Conversation.video_id == video_id)
            .order_by(Conversation.updated_at.desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def create(self, video_id: uuid.UUID, title: str = "New conversation") -> Conversation:
        conversation = Conversation(video_id=video_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        await self.session.delete(conversation)

    async def recent_messages(self, conversation_id: uuid.UUID, limit: int) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def add_message(self, conversation_id: uuid.UUID, role: str, content: str, **extra) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content, **extra)
        self.session.add(message)
        await self.session.flush()
        return message
