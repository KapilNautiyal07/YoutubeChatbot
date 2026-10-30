import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from app.api.routes import chat, conversations, providers, videos
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.session import engine

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting %s | chat provider=%s | embeddings=%s", settings.app_name, settings.llm_provider,
        settings.active_embedding_model,
    )
    for name, key in (("GROQ_API_KEY", settings.groq_api_key), ("GEMINI_API_KEY", settings.gemini_api_key)):
        if not key:
            logger.warning("%s is not set; that provider will be unavailable.", name)
    yield
    await engine.dispose()


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return _error(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "request"
    return _error(422, "validation_error", f"Invalid {field}: {first.get('msg', 'invalid value')}")


@app.exception_handler(OperationalError)
@app.exception_handler(DBAPIError)
async def database_error_handler(_: Request, exc: Exception):
    logger.error("Database error: %s", type(exc).__name__)
    return _error(503, "database_unavailable", "The database is unavailable right now. Please try again shortly.")


@app.exception_handler(OSError)
async def connection_error_handler(_: Request, exc: OSError):
    logger.error("Connection error: %s", exc)
    return _error(503, "service_unavailable", "A backend service is unreachable. Please try again shortly.")


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return _error(500, "internal_error", "Something went wrong on our side. Please try again.")


api = APIRouter(prefix="/api")
api.include_router(videos.router)
api.include_router(chat.router)
api.include_router(conversations.router)
api.include_router(providers.router)


@api.get("/health", tags=["health"])
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db = "ok"
    except Exception:
        db = "unavailable"
    return {"status": "ok" if db == "ok" else "degraded", "database": db}


app.include_router(api)
