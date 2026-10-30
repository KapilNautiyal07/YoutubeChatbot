# Tubewise — talk to any YouTube video

Paste a YouTube link, and Tubewise reads the full transcript, indexes it in PostgreSQL (pgvector), and lets you
have a grounded conversation with the video. Every answer cites timestamps you can click to jump the embedded
player to that moment.

- **Backend:** FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL + pgvector
- **AI:** Groq or Google Gemini for chat (switchable per message) · Gemini embeddings (or optional local embeddings)
- **Frontend:** React · TypeScript · Tailwind CSS v4 · React Router · Axios

## How it works

```
URL ─► video ID ─► metadata (oEmbed + watch page) ─► transcript (youtube-transcript-api)
    ─► clean + sentence-aware chunks with start/end times ─► embeddings ─► PostgreSQL/pgvector

Question ─► (follow-up rewrite using chat history) ─► query embedding (same model as the index)
         ─► hybrid retrieval: pgvector cosine + Postgres full-text, fused with RRF
         ─► neighbor expansion (or timeline coverage for "summarize"-type questions)
         ─► grounded prompt ─► Groq / Gemini (streamed) ─► answer with [mm:ss] citations
```

Key design decisions:

- **Embedding consistency.** Each chunk and video stores its `embedding_model` (e.g. `gemini:gemini-embedding-001@768`).
  Queries are always embedded with the model the video was indexed with, even if you change `.env` later.
  Re-process a video (Try again / `POST /api/videos/{id}/reindex`) to move it to the new model.
- **Chat providers are independent of embeddings.** Switching Groq ↔ Gemini never requires re-indexing.
- **Whole-video questions** ("summarize", "key takeaways") are detected. If the transcript fits in
  `MAX_CONTEXT_CHARS`, the model sees the *entire* transcript; otherwise chunks are sampled evenly across the
  timeline alongside the best matches.
- **Exact vector search per video.** Retrieval is always filtered to one video, so an exact scan (indexed by
  `video_id, embedding_model`) is fast and more accurate than a filtered ANN index.
- **Async ingestion.** `POST /api/videos/process` returns immediately; a background task updates the video's
  `status` (`pending → fetching_transcript → embedding → ready | failed`), which the UI polls.

## Prerequisites

- Python 3.11+ (tested on 3.13)
- Node.js 20+ (tested on 24)
- PostgreSQL 14+ with the [pgvector](https://github.com/pgvector/pgvector) extension available
- API keys: [Groq](https://console.groq.com/keys) and/or [Google AI Studio (Gemini)](https://aistudio.google.com/apikey).
  A Gemini key is required for the default embedding provider.

## Setup

### 1. Database

```sql
-- in psql as a superuser
CREATE DATABASE youtube_chatbot;
```

The first migration runs `CREATE EXTENSION IF NOT EXISTS vector`, which needs a role allowed to create extensions.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in DATABASE_URL, GROQ_API_KEY, GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs · health check: http://localhost:8000/api/health

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to `http://localhost:8000`
(override with `VITE_BACKEND_URL`, or set `VITE_API_URL` for a deployed backend).

### Tests

```bash
cd backend
pytest
```

## Configuration

All settings live in `backend/.env` (see `.env.example`). The most useful ones:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_PROVIDER` | `groq` | Default chat provider when the UI doesn't specify one |
| `GROQ_CHAT_MODEL` / `GEMINI_CHAT_MODEL` | `llama-3.3-70b-versatile` / `gemini-2.5-flash` | Default model per provider (the UI lists all models your key can use) |
| `EMBEDDING_PROVIDER` | `gemini` | `gemini` or `local` (`pip install -r requirements-local.txt`) |
| `GEMINI_EMBEDDING_MODEL`, `EMBEDDING_DIMENSION` | `gemini-embedding-001`, `768` | Embedding model and output size |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | `1000`, `150` | Chunk size and overlap, in characters |
| `TOP_K`, `SIMILARITY_THRESHOLD` | `6`, `0.3` | Retrieval depth and minimum cosine similarity |
| `RERANK_ENABLED` | `true` | Fuse semantic and keyword rankings |
| `MAX_CONTEXT_CHARS` | `24000` | Transcript text sent per answer. Lower it if you hit Groq free-tier token limits |
| `PREFERRED_LANGUAGES` | `["en","en-US","en-GB"]` | Transcript languages to prefer; otherwise the original language is used |

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/videos/process` | `{url, language?, force?}` → starts processing (202) or returns the existing video |
| `GET` | `/api/videos` | Processed videos, most recent first |
| `GET` | `/api/videos/{id}` | Video details and processing status |
| `DELETE` | `/api/videos/{id}` | Delete a video with its chunks and conversations |
| `POST` | `/api/videos/{id}/reindex` | Re-process with current settings |
| `POST` | `/api/videos/{id}/suggested-questions` | Generated starter questions (cached) |
| `GET` | `/api/videos/{id}/conversations` | Conversations for a video |
| `POST` | `/api/chat` | `{video_id, conversation_id?, question, provider?, model?}` → grounded answer + sources |
| `POST` | `/api/chat/stream` | Same, as server-sent events: `meta`, `token`…, `done` / `error` |
| `GET` / `DELETE` | `/api/conversations/{id}` | Conversation history / delete |
| `GET` | `/api/providers`, `/api/providers/{name}/models` | Configured providers and available models |

Errors use one shape: `{"error": {"code": "...", "message": "..."}}`. Messages are safe to show to users.
API keys and stack traces are never returned.

## Project structure

```
backend/
  app/
    api/routes/          videos, chat (incl. SSE), conversations, providers
    core/                settings, logging, errors, rate limiting
    db/                  models, async session, repositories
    services/
      youtube/           URL parsing, metadata, transcripts
      processing/        timestamp-preserving chunker
      embeddings/        EmbeddingProvider → Gemini, Local; factory
      llm/               LLMProvider → Groq, Gemini; provider registry
      retrieval/         hybrid retriever
      rag/               prompts and pipeline orchestration
      ingestion.py       background processing job
  alembic/               migrations
  tests/
frontend/
  src/
    api/                 typed API client and SSE streaming
    components/          chat, video, and UI components
    context/             provider/model selection
    hooks/, lib/, pages/
```

## Adding a chat provider

1. Implement `LLMProvider` (`generate`, `stream`, `list_models`) in `backend/app/services/llm/`.
2. Register it in `PROVIDERS` in `backend/app/services/llm/factory.py` with its key and default model settings.

It then shows up in the UI's provider menu automatically.

## Known limitations

- Only videos with captions (manual or auto-generated) can be processed. Audio isn't transcribed.
- YouTube may block transcript requests from cloud/datacenter IPs. Running locally is usually fine. For servers,
  `youtube-transcript-api` supports proxies.
- The in-memory rate limiter and background jobs assume a single server process. Jobs interrupted by a restart
  resume when the video is next opened.
- Free-tier Groq and Gemini keys have tight rate limits. Embedding requests retry with backoff, and chat errors
  explain when a limit was hit.
