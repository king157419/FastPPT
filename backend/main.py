from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.upload import router as upload_router
from api.chat import router as chat_router
from api.generate import router as generate_router
from api.download import router as download_router
from api.asr import router as asr_router
from api.retrieval import router as retrieval_router
from api.knowledge import router as knowledge_router

from core.monitoring import (
    monitoring_middleware,
    health_check,
    export_prometheus_metrics,
    error_tracker,
    performance_monitor,
    setup_logging
)

# Initialize logging
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/fastppt.log" if os.getenv("APP_ENV") == "production" else None
)

app = FastAPI(
    title="FastPPT API",
    description="AI-powered presentation generation system",
    version="1.0.0"
)

# Add monitoring middleware
app.middleware("http")(monitoring_middleware)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Include API routers
app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(download_router, prefix="/api")
app.include_router(asr_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api/retrieval")
app.include_router(knowledge_router, prefix="/api")


def _agent_enabled() -> bool:
    return os.getenv("ENABLE_AGENT", "false").strip().lower() == "true"


def _contest_force_plain() -> bool:
    return os.getenv("CONTEST_FORCE_PLAIN", "true").strip().lower() == "true"


def _agent_router_enabled() -> bool:
    return _agent_enabled() and not _contest_force_plain()


if _agent_router_enabled():
    from api.agent import router as agent_router

    app.include_router(agent_router, prefix="/api")


def _resolve_rag_mode() -> str:
    if (
        os.getenv("RAGFLOW_BASE_URL", "").strip()
        and os.getenv("RAGFLOW_API_KEY", "").strip()
        and os.getenv("RAGFLOW_KB_ID", "").strip()
    ):
        return "ragflow"
    if os.getenv("DASHSCOPE_API_KEY", "").strip():
        return "vector"
    return "tfidf"


def _resolve_ppt_export_mode() -> str:
    if os.getenv("PPTXGENJS_SERVICE_URL", "").strip():
        return "pptxgenjs+python-pptx-fallback"
    return "python-pptx"


@app.get("/")
def root():
    return {"status": "ok", "message": "FastPPT backend running"}


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    payload = await health_check()
    agent_enabled = _agent_router_enabled()
    contest_force_plain = _contest_force_plain()
    redis_configured = bool(os.getenv("REDIS_URL", "").strip())
    rag_mode = _resolve_rag_mode()
    payload.update(
        {
            "chat_mode": "agent" if agent_enabled else "plain",
            "agent_enabled": agent_enabled,
            "contest_force_plain": contest_force_plain,
            "redis": "configured" if redis_configured else "skipped",
            "rag_mode": rag_mode,
            "ppt_export": _resolve_ppt_export_mode(),
            "demo_mode": (not agent_enabled and not redis_configured and rag_mode == "tfidf"),
        }
    )
    return payload


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return export_prometheus_metrics()


@app.get("/admin/errors")
async def get_errors(endpoint: str = None, limit: int = 50):
    """Get recent errors for debugging."""
    return {
        "errors": error_tracker.get_errors(endpoint, limit),
        "summary": error_tracker.get_error_summary()
    }


@app.get("/admin/performance")
async def get_performance(endpoint: str = None):
    """Get performance statistics."""
    return performance_monitor.get_stats(endpoint)
