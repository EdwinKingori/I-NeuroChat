from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# from app.api.v1 import api_router
from core.logging_config import setup_logging
from core.middleware import RequestLoggingMiddleware
from core.redis_config import redis_client

# ✅ Initializing logging
setup_logging()
logger = logging.getLogger(__name__)


# ✅ === LIFESPAN CONTEXT MANAGER ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    logger.info("✅ Application startup completed.")
    yield
    await redis_client.close()
    logger.info("🛑 Application shutdown initiated.")


# ✅ APP INITIALIZATION
app = FastAPI(
    title="I-NeuroChat API",
    description="Real-time chat API with LLM integration, audio support, and user memory",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ === CORS MIDDLEWARE ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Registering the middleware
app.add_middleware(RequestLoggingMiddleware)


# ✅ === INCLUDE API ROUTERS ===
# app.include_router(
#     api_router,
#     prefix="/api/v1",
#     tags=["v1"]
# )

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"


# ✅ === HEALTH CHECK ENDPOINT ===
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    logger.info(f"{BOLD}{CYAN}</>{RESET}  Health check accessed!")
    return {
        "status": "healthy",
        "service": "INeuroChat API",
        "version": "1.0.0"
    }


# ✅ === ROOT ENDPOINT ===
@app.get("/")
async def root_status():
    logger.info(f"{BOLD}{CYAN}</>{RESET} Root endpoint accessed!")
    return {
        "message": "Welcome to the AI-Chat Agent API! Redis Configured",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
