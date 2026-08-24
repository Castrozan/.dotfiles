from __future__ import annotations

import time
from datetime import datetime


class SystemClock:
    def formatted_now(self, pattern: str) -> str:
        return datetime.now().strftime(pattern)

    def monotonic_seconds(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
