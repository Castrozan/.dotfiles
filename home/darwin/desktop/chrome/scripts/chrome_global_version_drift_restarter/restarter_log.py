from __future__ import annotations


def log_event(message: str) -> None:
    print(f"[chrome-global-version-drift-restarter] {message}", flush=True)
