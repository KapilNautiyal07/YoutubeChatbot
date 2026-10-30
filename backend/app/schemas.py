import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProcessVideoRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="YouTube URL or video ID")
    language: str | None = Field(None, pattern=r"^[A-Za-z]{2,3}([-_][A-Za-z0-9]{2,8})?$")
    force: bool = Field(False, description="Re-process even if the video was already indexed")


class VideoOut(ORMModel):
    id: uuid.UUID
    youtube_video_id: str
    title: str | None
    channel_name: str | None
    thumbnail_url: str | None
    duration: int | None
    transcript_language: str | None
    transcript_language_code: str | None
    transcript_is_generated: bool | None
    transcript_is_translated: bool
    status: str
    status_message: str | None
    error_message: str | None
    embedding_model: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class ProcessVideoResponse(BaseModel):
    video: VideoOut
    created: bool
    message: str


class SourceOut(BaseModel):
    chunk_index: int
    start_time: float
    end_time: float
    score: float | None = None
    content: str


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    sources: list[SourceOut] = []
    created_at: datetime


class ConversationOut(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class ChatRequest(BaseModel):
    video_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    question: str = Field(..., min_length=1, max_length=4000)
    provider: str | None = Field(None, max_length=32)
    model: str | None = Field(None, max_length=128)


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    user_message_id: uuid.UUID
    message: MessageOut


class SuggestedQuestionsRequest(BaseModel):
    provider: str | None = Field(None, max_length=32)
    force: bool = False


class SuggestedQuestionsResponse(BaseModel):
    questions: list[str]


class ProviderOut(BaseModel):
    name: str
    label: str
    description: str
    configured: bool
    default_model: str


class ProvidersResponse(BaseModel):
    default_provider: str
    embedding_model: str
    providers: list[ProviderOut]


class ModelsResponse(BaseModel):
    provider: str
    default_model: str
    models: list[str]
