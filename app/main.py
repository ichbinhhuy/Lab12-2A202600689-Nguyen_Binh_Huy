from __future__ import annotations

import os
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import redis

from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.recommend import router as recommend_router
from app.api.seed_cafes import router as seed_cafes_router
from app.core.config import get_settings
from app.repositories.cafe_repository import CafeRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.services.feedback_service import FeedbackService
from app.services.reason_service import ReasonService
from app.services.recommendation_service import RecommendationService
from app.services.seed_cafe_service import SeedCafeService

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
# Config logging dynamically to prevent import-time side effects
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "true").lower() == "true" else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0
r = None

# ─────────────────────────────────────────────────────────
# Stateless Rate Limiter (Redis)
# ─────────────────────────────────────────────────────────
def check_rate_limit(key: str):
    settings = get_settings()
    now = time.time()
    redis_key = f"rate:{key}"
    try:
        if r:
            # Remove old entries
            r.zremrangebyscore(redis_key, 0, now - 60)
            # Check limit
            current = r.zcard(redis_key)
            if current >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                    headers={"Retry-After": "60"},
                )
            # Add new entry
            r.zadd(redis_key, {str(now): now})
            r.expire(redis_key, 60)
    except redis.RedisError as e:
        # Fallback to local keyless if redis is not running
        logger.warning(f"Redis rate limit fail: {e}")

# ─────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    settings = get_settings()
    # permissive check to not break UI calls (since UI has no API key configuration)
    if api_key and api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Include header: X-API-Key: <key>",
        )
    return api_key or "default"

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready, r
    settings = get_settings()
    
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "environment": settings.environment,
    }))

    # Set up Redis client dynamically inside lifespan
    r = redis.from_url(settings.redis_url)

    cafe_repository = CafeRepository(settings.cafes_path)
    feedback_repository = FeedbackRepository(settings.feedback_log_path)

    app.state.seed_cafe_service = SeedCafeService(
        repository=cafe_repository,
        default_seed_count=settings.seed_count,
    )
    app.state.recommendation_service = RecommendationService(
        cafe_repository=cafe_repository,
        reason_service=ReasonService(),
        similarity_threshold=settings.similarity_threshold,
        max_results=settings.max_results,
    )
    app.state.feedback_service = FeedbackService(feedback_repository)

    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["Operations"])
    def health():
        """Liveness probe. Platform restarts container if this fails."""
        return {
            "status": "ok",
            "uptime_seconds": round(time.time() - START_TIME, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/ready", tags=["Operations"])
    def ready():
        """Readiness probe. Load balancer stops routing here if not ready."""
        if not _is_ready:
            raise HTTPException(503, "Not ready")
        try:
            if r:
                r.ping()
            else:
                raise ValueError("Redis client not initialized")
        except Exception as e:
            raise HTTPException(503, f"Redis not ready: {e}")
        return {"ready": True}

    app.include_router(health_router)
    app.include_router(seed_cafes_router)
    app.include_router(recommend_router)
    app.include_router(feedback_router)

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        global _request_count, _error_count
        start = time.time()
        _request_count += 1
        try:
            response: Response = await call_next(request)
            duration = round((time.time() - start) * 1000, 1)
            logger.info(json.dumps({
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": duration,
            }))
            return response
        except Exception as e:
            _error_count += 1
            raise

    return app

app = create_app()

# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)
