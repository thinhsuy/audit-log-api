from slowapi import Limiter
from slowapi.util import get_remote_address
from core.config import RATE_LIMIT_DEFAULT


class RateLimiter:
    def __init__(self, default_limit: str = None):
        self.default_limit: str = default_limit or RATE_LIMIT_DEFAULT
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[RATE_LIMIT_DEFAULT],
        )

    def get_limiter(self) -> Limiter:
        return self.limiter


RATE_LIMITER = RateLimiter(default_limit=RATE_LIMIT_DEFAULT)
