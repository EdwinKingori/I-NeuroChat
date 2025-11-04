from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


# Logging requests and responses in JSON format
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)
        process_time = round(time.time() - start_time, 4)

        log_data = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "status_code": response.status_code,
            "latency_seconds": process_time,
        }

        logger.info(log_data)
        return response
