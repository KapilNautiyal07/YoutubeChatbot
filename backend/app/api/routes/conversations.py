import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import message_to_out
from app.core.errors import NotFoundError
from app.db.repositories import ConversationRepository
from app.db.session import get_session
from app.schemas import ConversationDetail

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    conversation = await ConversationRepository(session).get(conversation_id, with_messages=True)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return ConversationDetail(
        id=conversation.id,
        video_id=conversation.video_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        messages=[message_to_out(m) for m in conversation.messages],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    repo = ConversationRepository(session)
    conversation = await repo.get(conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    await repo.delete(conversation)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
