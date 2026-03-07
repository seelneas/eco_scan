"""
EcoScan FastAPI Application (Phase 7 — Streaming, Rate Limiting, Privacy)
Main entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import router
from app.api.middleware import RequestLoggingMiddleware
from app.models.database import get_engine, create_tables

# ──────────────────────────────────────────
# Logging
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ecoscan")

# ──────────────────────────────────────────
# Settings
# ──────────────────────────────────────────
settings = get_settings()


# ──────────────────────────────────────────
# Lifespan (startup + shutdown)
# ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler replacing deprecated on_event."""
    # Startup
    logger.info("=" * 50)
    logger.info(f"  🌿 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  📡 Environment: {settings.ENVIRONMENT}")
    logger.info(f"  🤖 LLM Model: {settings.LLM_MODEL}")
    logger.info(f"  🗄️  Database: SQLite (ecoscan.db)")
    logger.info(f"  🔐 API Keys: {'Configured' if settings.API_KEYS else 'Open (dev mode)'}")
    logger.info(f"  ⏱️  Rate Limit: {settings.RATE_LIMIT_ANALYZE} analyze / {settings.RATE_LIMIT_WINDOW}s")
    logger.info(f"  🌊 Streaming: Enabled (SSE)")
    logger.info("=" * 50)

    # Ensure database tables exist
    engine = get_engine("sqlite:///./ecoscan.db")
    create_tables(engine)
    logger.info("  ✅ Database tables verified")

    yield

    # Shutdown
    logger.info("🌿 EcoScan shutting down...")


# ──────────────────────────────────────────
# App Factory
# ──────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered sustainability intelligence API for the EcoScan Chrome Extension.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ──────────────────────────────────────────
# Middleware Stack (order matters: last added = first executed)
# ──────────────────────────────────────────

# 1. CORS (must run before everything)
raw_origins = settings.CORS_ORIGINS.split(",")
origins = [o.strip() for o in raw_origins if o.strip()]
if not origins:
    origins = ["*"]

# CORS rules: if using "*", allow_credentials MUST be False
allow_credentials = True
if "*" in origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)

logger.info(f"  🔒 CORS: {origins} (Credentials: {allow_credentials})")

# 2. Request logging + error handling
app.add_middleware(RequestLoggingMiddleware)

# ──────────────────────────────────────────
# Routes
# ──────────────────────────────────────────
app.include_router(router, prefix="/api/v1", tags=["Analysis"])


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "analyze_stream": "/api/v1/analyze/stream",
            "feedback": "/api/v1/feedback",
            "health": "/api/v1/health",
            "brands": "/api/v1/brands",
        },
    }
