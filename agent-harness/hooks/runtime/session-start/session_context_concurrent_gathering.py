"""Run independent, subprocess-bound context probes at the same time."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


def gather_concurrently(callables_by_key):
    if not callables_by_key:
        return {}
    with ThreadPoolExecutor(max_workers=len(callables_by_key)) as executor:
        futures_by_key = {
            key: executor.submit(gatherer) for key, gatherer in callables_by_key.items()
        }
        return {key: future.result() for key, future in futures_by_key.items()}
