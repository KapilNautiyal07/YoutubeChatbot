"""Initial schema: videos, transcript chunks (pgvector), conversations, messages.

Revision ID: 0001
Revises:
Create Date: 2026-10-31
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("youtube_video_id", sa.String(16), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("channel_name", sa.Text()),
        sa.Column("thumbnail_url", sa.Text()),
        sa.Column("duration", sa.Integer()),
        sa.Column("transcript_language", sa.String(64)),
        sa.Column("transcript_language_code", sa.String(16)),
        sa.Column("transcript_is_generated", sa.Boolean()),
        sa.Column("transcript_is_translated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("status_message", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("embedding_model", sa.String(128)),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("transcript_chars", sa.Integer(), server_default="0", nullable=False),
        sa.Column("suggested_questions", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)
    op.create_index("ix_videos_status", "videos", ["status"])

    op.create_table(
        "transcript_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("embedding", Vector()),
        sa.Column("embedding_model", sa.String(128)),
        sa.Column(
            "content_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', content)", persisted=True),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("video_id", "chunk_index", name="uq_chunk_video_index"),
    )
    op.create_index("ix_chunks_video_model", "transcript_chunks", ["video_id", "embedding_model"])
    op.create_index("ix_chunks_content_tsv", "transcript_chunks", ["content_tsv"], postgresql_using="gin")

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.Text(), nullable=False, server_default="New conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conversations_video_id", "conversations", ["video_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(32)),
        sa.Column("model", sa.String(128)),
        sa.Column("retrieved_chunks", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("transcript_chunks")
    op.drop_table("videos")
