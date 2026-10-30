import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import process_rate_limit
from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.models import VideoStatus
from app.db.repositories import ConversationRepository, VideoRepository
from app.db.session import get_session
from app.schemas import (
    ConversationOut,
    ProcessVideoRequest,
    ProcessVideoResponse,
    SuggestedQuestionsRequest,
    SuggestedQuestionsResponse,
    VideoOut,
)
from app.services import ingestion
from app.services.rag.pipeline import generate_suggested_questions
from app.services.youtube.url import extract_video_id

router = APIRouter(prefix="/videos", tags=["videos"])


async def _get_video_or_404(session: AsyncSession, video_id: uuid.UUID):
    video = await VideoRepository(session).get(video_id)
    if video is None:
        raise NotFoundError("Video not found.")
    return video


async def _restart(session: AsyncSession, video, language: str | None) -> None:
    await VideoRepository(session).update_fields(
        video.id, status=VideoStatus.PENDING.value, status_message="Queued…", error_message=None
    )
    await session.commit()
    ingestion.schedule_ingestion(video.id, video.youtube_video_id, language)


@router.post(
    "/process",
    response_model=ProcessVideoResponse,
    dependencies=[Depends(process_rate_limit)],
    responses={202: {"model": ProcessVideoResponse}},
)
async def process_video(payload: ProcessVideoRequest, response: Response, session: AsyncSession = Depends(get_session)):
    youtube_id = extract_video_id(payload.url)
    repo = VideoRepository(session)
    video = await repo.get_by_youtube_id(youtube_id)

    if video is not None:
        in_progress = video.status in ingestion.IN_PROGRESS
        if in_progress and ingestion.is_running(video.id):
            response.status_code = status.HTTP_202_ACCEPTED
            return ProcessVideoResponse(video=VideoOut.model_validate(video), created=False,
                                        message="This video is already being processed.")
        if video.status == VideoStatus.READY.value and not payload.force:
            return ProcessVideoResponse(video=VideoOut.model_validate(video), created=False,
                                        message="This video is already ready to chat.")
        # Failed, forced, or interrupted by a server restart: process again.
        await _restart(session, video, payload.language)
        await session.refresh(video)
        response.status_code = status.HTTP_202_ACCEPTED
        return ProcessVideoResponse(video=VideoOut.model_validate(video), created=False, message="Processing started.")

    try:
        video = await repo.create(youtube_id)
        video.status_message = "Queued…"
        await session.commit()
    except IntegrityError:
        # A concurrent request created the same video first.
        await session.rollback()
        video = await repo.get_by_youtube_id(youtube_id)
        response.status_code = status.HTTP_202_ACCEPTED
        return ProcessVideoResponse(video=VideoOut.model_validate(video), created=False,
                                    message="This video is already being processed.")

    await session.refresh(video)
    ingestion.schedule_ingestion(video.id, youtube_id, payload.language)
    response.status_code = status.HTTP_202_ACCEPTED
    return ProcessVideoResponse(video=VideoOut.model_validate(video), created=True, message="Processing started.")


@router.get("", response_model=list[VideoOut])
async def list_videos(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)):
    limit = max(1, min(limit, 100))
    return await VideoRepository(session).list(limit=limit, offset=max(0, offset))


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(video_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    video = await _get_video_or_404(session, video_id)
    # Recover from jobs interrupted by a server restart.
    if video.status in ingestion.IN_PROGRESS and not ingestion.is_running(video.id):
        await _restart(session, video, None)
        await session.refresh(video)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    video = await _get_video_or_404(session, video_id)
    ingestion.cancel(video.id)
    await VideoRepository(session).delete(video)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{video_id}/reindex", response_model=ProcessVideoResponse, status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(process_rate_limit)])
async def reindex_video(video_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    video = await _get_video_or_404(session, video_id)
    if not ingestion.is_running(video.id):
        await _restart(session, video, video.transcript_language_code)
        await session.refresh(video)
    return ProcessVideoResponse(video=VideoOut.model_validate(video), created=False, message="Re-indexing started.")


@router.post("/{video_id}/suggested-questions", response_model=SuggestedQuestionsResponse)
async def suggested_questions(
    video_id: uuid.UUID, payload: SuggestedQuestionsRequest | None = None, session: AsyncSession = Depends(get_session)
):
    payload = payload or SuggestedQuestionsRequest()
    video = await _get_video_or_404(session, video_id)
    if video.status != VideoStatus.READY.value:
        return SuggestedQuestionsResponse(questions=[])
    questions = await generate_suggested_questions(session, get_settings(), video, payload.provider, payload.force)
    return SuggestedQuestionsResponse(questions=questions)


@router.get("/{video_id}/conversations", response_model=list[ConversationOut])
async def list_conversations(video_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await _get_video_or_404(session, video_id)
    rows = await ConversationRepository(session).list_for_video(video_id)
    return [
        ConversationOut(
            id=c.id, video_id=c.video_id, title=c.title, created_at=c.created_at, updated_at=c.updated_at,
            message_count=count,
        )
        for c, count in rows
    ]
