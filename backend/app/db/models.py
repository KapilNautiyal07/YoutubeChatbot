import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    FETCHING_TRANSCRIPT = "fetching_transcript"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_video_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    channel_name: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[int | None] = mapped_column(Integer)  # seconds
    transcript_language: Mapped[str | None] = mapped_column(String(64))
    transcript_language_code: Mapped[str | None] = mapped_column(String(16))
    transcript_is_generated: Mapped[bool | None] = mapped_column(Boolean)
    transcript_is_translated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(32), default=VideoStatus.PENDING.value, index=True)
    status_message: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    transcript_chars: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    suggested_questions: Mapped[list[str] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks: Mapped[list["TranscriptChunk"]] = relationship(
        back_populates="video", cascade="all, delete-orphan", passive_deletes=True
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="video", cascade="all, delete-orphan", passive_deletes=True
    )


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    __table_args__ = (
        UniqueConstraint("video_id", "chunk_index", name="uq_chunk_video_index"),
        Index("ix_chunks_video_model", "video_id", "embedding_model"),
        Index("ix_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    # Dimension is intentionally unconstrained so different embedding models can coexist.
    embedding = mapped_column(Vector(), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    content_tsv = mapped_column(TSVECTOR, Computed("to_tsvector('simple', content)", persisted=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    video: Mapped[Video] = relationship(back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    video: Mapped[Video] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(128))
    retrieved_chunks: Mapped[list[dict] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
