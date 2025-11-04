from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import logging

from core.logging_config import setup_logging
from core.middleware import RequestLoggingMiddleware

# ✅ Initializing logging
setup_logging()
logger = logging.getLogger(__name__)


# ✅ Startup and Shuttding down logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Application startup completed.")
    yield
    logger.info("🛑 Application shutdown initiated.")

app = FastAPI(lifespan=lifespan)

# ✅ Registering the middleware
app.add_middleware(RequestLoggingMiddleware)

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"


# ✅ Health status checking
@app.get("/")
async def root_status():
    logger.info(f"{BOLD}{CYAN}</>{RESET} Root endpoint accessed")
    return {"message": "Welcome to the AI-Chat Agent API!"}
