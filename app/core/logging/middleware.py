import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from app.core.logging.context import set_request_context
from app.core.logging.route_logger import get_route_logger


logger = get_route_logger("http")

# JWT Configuration
JWT_SELECT = "CHANGE_LATER"
JWT_ALGORITHM = "Hs256"

# Logging requests and responses in JSON format
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):

        # 1️⃣ Generating request correlation ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # 2️⃣ Initializing user context placeholders
        user_id = None
        user_email = None
        user_role = None

         # 3️⃣ Attempting JWT extraction -> this does not enforce authentication
        # ↪ It only enriches logs if token exists
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("")[1]

            try:
                payload = jwt.decode(
                    token,
                    JWT_SELECT,
                    algorithms=[JWT_ALGORITHM],
                    options={"verify_aud":False}
                )

                user_id = payload.get("sub")
                user_email = payload.get("email")
                user_role = payload.get("role")
            except JWTError:
                # NOTE: Logging must NEVER break the request flow
                pass

        # 4️⃣ Storing context for entire request lifecycle:
        # This request is available everywhere including services, repositories, background jobs, etc

        set_request_context(
            request_id=request_id,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role
        )

        # 5️⃣ Continue with request processing
        response = await call_next(request)

        # 6️⃣ Measuring latency
        process_time = round(time.time() - start_time, 4)

         # 7️⃣ Attaching request_id to response
        response.headers["X-Request-ID"] = request_id

        # 8️⃣ Log HTTP summary
        logger.info(
            "HTTP request processed",
            extra = {
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "status_code": response.status_code,
                "latency_seconds": process_time,
                "user_agent": request.headers.get("user-agent"),
            },
        )


        return response
