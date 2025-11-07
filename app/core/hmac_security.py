import hmac
import hashlib
from .config import get_settings

settings = get_settings()


# ✅ Preventing key collision attacks + hiding real keys
def hmac_key(key: str) -> str:
    return hmac.new(
        settings.REDIS_HMAC_SECRET.encode(),
        key.encode(),
        hashlib.sha256
    ).hexdigest()
