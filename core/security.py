from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict
from urllib.parse import urlparse

from fastapi import HTTPException


_ALLOWED_SCHEMES = {"http", "https"}
_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+$")


class SimpleRateLimiter:
    def __init__(self) -> None:
        self._window_hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.time()
        window = self._window_hits[key]

        while window and window[0] <= now - window_seconds:
            window.popleft()

        if len(window) >= limit:
            return False

        window.append(now)
        return True


rate_limiter = SimpleRateLimiter()


def sanitize_url_input(url: str) -> str:
    candidate = (url or "").strip()
    if not candidate:
        raise HTTPException(status_code=400, detail="URL is required")

    parsed = urlparse(candidate)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")

    if not parsed.netloc or not _DOMAIN_RE.match(parsed.netloc.replace(":", "")):
        raise HTTPException(status_code=400, detail="Invalid host in URL")

    return candidate
