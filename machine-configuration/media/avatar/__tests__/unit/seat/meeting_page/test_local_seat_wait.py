from unittest.mock import Mock

import local_seat
import pytest


@pytest.fixture(autouse=True)
def no_real_sleeping(monkeypatch):
    monkeypatch.setattr(local_seat.time, "sleep", Mock())


def test_waiting_returns_as_soon_as_the_condition_holds():
    answers = iter([False, False, True])
    local_seat.wait_until(lambda: next(answers), 5, "never")


def test_waiting_past_the_deadline_raises_the_given_message():
    with pytest.raises(TimeoutError, match="gave up"):
        local_seat.wait_until(lambda: False, -1, "gave up")


def test_the_tunnel_counts_as_open_once_the_seat_answers(monkeypatch):
    answers = iter([None, {"attached": False}])
    monkeypatch.setattr(local_seat, "health", lambda: next(answers))
    local_seat.wait_for_tunnel()


def test_a_tunnel_that_never_opens_times_out(monkeypatch):
    monkeypatch.setattr(local_seat, "health", lambda: None)
    monkeypatch.setattr(local_seat, "TUNNEL_WAIT_SECONDS", -1)
    with pytest.raises(TimeoutError, match="tunnel"):
        local_seat.wait_for_tunnel()
