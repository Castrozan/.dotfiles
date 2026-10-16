from types import SimpleNamespace

import pytest

from e2e.sessions import e2e_herdr_io


@pytest.fixture
def simulated_monotonic_clock(monkeypatch):
    elapsed_seconds = 0.0

    def advance_time(seconds):
        nonlocal elapsed_seconds
        elapsed_seconds += seconds

    monkeypatch.setattr(
        e2e_herdr_io,
        "time",
        SimpleNamespace(monotonic=lambda: elapsed_seconds, sleep=advance_time),
    )
