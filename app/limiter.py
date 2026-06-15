import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_STRICT_ENVS = {"production", "prod", "staging"}
_rate_limiting_enabled = os.getenv("APP_ENV", "development").lower() in _STRICT_ENVS

limiter = Limiter(key_func=get_remote_address, enabled=_rate_limiting_enabled)
