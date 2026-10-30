import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TranscriptChunk, Video


class VideoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, video_id: uuid.UUID) -> Video | None:
        return await self.session.get(Video, video_id)

    async def get_by_youtube_id(self, youtube_video_id: str) -> Video | None:
        result = await self.session.execute(select(Video).where(Video.youtube_video_id == youtube_video_id))
        return result.scalar_one_or_none()

    async def list(self, limit: int = 50, offset: int = 0) -> Sequence[Video]:
        result = await self.session.execute(
            select(Video).order_by(Video.updated_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def create(self, youtube_video_id: str) -> Video:
        video = Video(youtube_video_id=youtube_video_id)
        self.session.add(video)
        await self.session.flush()
        return video

    async def update_fields(self, video_id: uuid.UUID, **fields) -> None:
        await self.session.execute(update(Video).where(Video.id == video_id).values(**fields))

    async def delete(self, video: Video) -> None:
        await self.session.delete(video)


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_for_video(self, video_id: uuid.UUID, chunks: list[TranscriptChunk]) -> None:
        await self.session.execute(delete(TranscriptChunk).where(TranscriptChunk.video_id == video_id))
        self.session.add_all(chunks)
        await self.session.flush()

    async def list_for_video(self, video_id: uuid.UUID) -> Sequence[TranscriptChunk]:
        result = await self.session.execute(
            select(TranscriptChunk)
            .where(TranscriptChunk.video_id == video_id)
            .order_by(TranscriptChunk.chunk_index)
        )
        return result.scalars().all()

    async def get_by_indexes(self, video_id: uuid.UUID, indexes: Sequence[int]) -> Sequence[TranscriptChunk]:
        if not indexes:
            return []
        result = await self.session.execute(
            select(TranscriptChunk)
            .where(TranscriptChunk.video_id == video_id, TranscriptChunk.chunk_index.in_(list(indexes)))
            .order_by(TranscriptChunk.chunk_index)
        )
        return result.scalars().all()
