from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user_session import UserSession


def extract_device_info(request: Request) -> dict:
    """Extract device metadata from request headers."""
    user_agent = (request.headers.get("user-agent", "") or "")[:512]

    # Respect X-Forwarded-For from reverse proxies
    x_forwarded = request.headers.get("x-forwarded-for", "")
    ip_address = (
        x_forwarded.split(",")[0].strip()
        if x_forwarded
        else (request.client.host if request.client else "")
    )[:45]

    # Optional client-supplied device fingerprint
    device_id = (request.headers.get("x-device-id", "") or "")[:128] or None

    return {
        "user_agent": user_agent or None,
        "ip_address": ip_address or None,
        "device_id": device_id,
        "device_name": _parse_device_name(user_agent),
    }


def _parse_device_name(user_agent: str) -> str:
    ua = user_agent.lower()
    if "android" in ua:
        return "Android Device"
    if "iphone" in ua:
        return "iPhone"
    if "ipad" in ua:
        return "iPad"
    if "mobile" in ua:
        return "Mobile Device"
    if "windows" in ua:
        return "Windows PC"
    if "macintosh" in ua or "mac os" in ua:
        return "Mac"
    if "linux" in ua:
        return "Linux"
    return "Unknown Device"


async def enforce_session_concurrency(
    db: AsyncSession,
    redis,
    user_id: str,
    max_sessions: int,
) -> None:
    """
    Revoke the oldest active sessions when the concurrency limit is reached,
    making room for the new session about to be created.
    """
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )
        .order_by(UserSession.created_at.asc())
    )
    active_sessions = result.scalars().all()

    # How many need to be revoked to keep total at (max_sessions - 1)
    excess = len(active_sessions) - max_sessions + 1
    if excess <= 0:
        return

    for session in active_sessions[:excess]:
        session.is_active = False
        await redis.delete(f"session:{session.session_key}")

    await db.flush()
