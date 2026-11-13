import asyncio
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import host_state
import pytest
from seat_page import SeatPage


def test_the_host_reads_whether_it_listens_and_whether_a_meeting_runs(monkeypatch):
    monkeypatch.setattr(host_state.listener_runtime, "listening", lambda: True)
    asked = Mock(return_value=False)
    monkeypatch.setattr(host_state.user_units, "unit_active", asked)
    assert host_state.read() == {"listening": True, "meeting": False}
    asked.assert_called_once_with("avatar.target")


def test_nothing_is_claimed_before_the_first_read():
    assert host_state.HostState().snapshot() == {"listening": False, "meeting": False}


def test_a_refresh_replaces_what_is_known():
    state = host_state.HostState(lambda: {"listening": True, "meeting": True})
    asyncio.run(state.refresh())
    assert state.snapshot() == {"listening": True, "meeting": True}


@pytest.mark.parametrize(
    "failure",
    [OSError("no systemd"), subprocess.TimeoutExpired("systemctl", 1), TimeoutError()],
)
def test_a_read_that_fails_keeps_what_was_known(failure):
    answers = [{"listening": True, "meeting": True}, failure]

    def read():
        answer = answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    state = host_state.HostState(read)
    asyncio.run(state.refresh())
    asyncio.run(state.refresh())
    assert state.snapshot() == {"listening": True, "meeting": True}


def test_a_snapshot_cannot_change_what_is_known():
    state = host_state.HostState()
    state.snapshot()["meeting"] = True
    assert state.snapshot()["meeting"] is False


def test_following_refreshes_at_a_bounded_pace(monkeypatch):
    reads = Mock(return_value={"listening": False, "meeting": True})
    pauses = []

    async def pause(seconds):
        pauses.append(seconds)
        if len(pauses) == 3:
            raise asyncio.CancelledError

    monkeypatch.setattr(host_state.asyncio, "sleep", pause)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(host_state.HostState(reads).follow())
    assert reads.call_count == 3
    assert pauses == [host_state.REFRESH_SECONDS] * 3


def test_the_seat_health_carries_the_host_state():
    page = SeatPage(
        {}, lambda: True, None, lambda: {"listening": True, "meeting": False}
    )
    answer = page.report_health(SimpleNamespace())
    assert json.loads(answer.body) == {
        "attached": True,
        "failure": None,
        "listening": True,
        "meeting": False,
    }


def test_a_page_without_a_host_reports_only_its_own_state():
    answer = SeatPage({}, lambda: False).report_health(SimpleNamespace())
    assert json.loads(answer.body) == {"attached": False, "failure": None}
