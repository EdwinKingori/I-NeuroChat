from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import logging

from app.core.logging.logging_config import setup_logging
from app.core.logging.middleware import RequestLoggingMiddleware
from app.core.redis.redis_config import redis_client
from app.api.v1 import (admin, messages, users, sessions)

# ✅ Initializing logging
setup_logging()
logger = logging.getLogger(__name__)


# ✅ Startup and Shuttding down logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    logger.info("✅ Application startup completed.")
    yield
    await redis_client.close()
    logger.info("🛑 Application shutdown initiated.")

app = FastAPI(
    lifespan=lifespan,
    title="I-NeuroChat API"
)

# ✅ Registering Routes
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(admin.router)

# ✅ Registering the middleware
app.add_middleware(RequestLoggingMiddleware)

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"


# ✅ Health status checking
@app.get("/health")
async def get_health_check():
    logger.info(f"{BOLD}{CYAN}</>{RESET} Health Status check")
    return {
        "message": "The AI-Chat Agent API is healthy!"
    }


# ✅ Welcoming Endpoint
@app.get("/")
async def root_status():
    logger.info(f"{BOLD}{CYAN}</>{RESET} Root endpoint accessed")
    return {"message": "Welcome to the AI-Chat Agent API! Redis Configured"}
