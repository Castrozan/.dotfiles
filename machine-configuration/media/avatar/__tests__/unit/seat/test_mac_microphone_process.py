from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import local_seat
import mac_microphone
import pytest


@pytest.fixture
def main_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("AVATAR_WAKE_PAGE", str(tmp_path))
    monkeypatch.setenv("AVATAR_SEAT_PAGE", str(tmp_path))
    registered = Mock()
    ended = Mock()
    monkeypatch.setattr(mac_microphone.signal, "signal", registered)
    monkeypatch.setattr(local_seat, "end_processes_matching", ended)
    return SimpleNamespace(registered=registered, ended=ended, patch=monkeypatch)


def run_main(environment, relay):
    environment.patch.setattr(mac_microphone, "relay_microphone", relay)
    with pytest.raises(SystemExit) as finished:
        mac_microphone.main()
    return finished.value.code


def test_a_page_that_never_attaches_exits_non_zero_and_closes_its_chrome(
    main_environment, capsys
):
    code = run_main(main_environment, AsyncMock(side_effect=TimeoutError("late")))
    assert code == 1
    assert mac_microphone.NO_PAGE_MESSAGE in capsys.readouterr().err
    main_environment.ended.assert_called_once_with(mac_microphone.WAKE_PROFILE_FLAG)


def test_terminating_closes_its_chrome_and_exits_at_once(main_environment, monkeypatch):
    left = Mock()
    monkeypatch.setattr(mac_microphone.os, "_exit", left)
    mac_microphone.end_on_terminate(None, None)
    main_environment.ended.assert_called_once_with(mac_microphone.WAKE_PROFILE_FLAG)
    left.assert_called_once_with(0)


def test_the_terminate_signal_is_handled_by_the_exit(main_environment):
    main_environment.patch.setattr(mac_microphone, "relay_microphone", AsyncMock())
    mac_microphone.main()
    main_environment.registered.assert_any_call(
        mac_microphone.signal.SIGTERM, mac_microphone.end_on_terminate
    )


def test_a_page_that_leaves_closes_its_chrome_and_ends_cleanly(main_environment):
    main_environment.patch.setattr(mac_microphone, "relay_microphone", AsyncMock())
    mac_microphone.main()
    main_environment.ended.assert_called_once_with(mac_microphone.WAKE_PROFILE_FLAG)


def test_the_page_opens_headless_on_its_own_profile_after_clearing_the_old_one(
    monkeypatch,
):
    order = Mock()
    monkeypatch.setattr(local_seat, "end_processes_matching", order.end)
    monkeypatch.setattr(local_seat.subprocess, "run", order.open)
    mac_microphone.open_microphone_page()
    assert [call[0] for call in order.mock_calls] == ["end", "open"]
    assert order.end.call_args.args == (mac_microphone.WAKE_PROFILE_FLAG,)
    command = order.open.call_args.args[0]
    assert "--headless=new" in command
    assert "--app=http://localhost:8771/" in command
    assert mac_microphone.WAKE_PROFILE_FLAG in command
    assert local_seat.BROWSER_PROFILE_FLAG not in command
    assert not any(flag.startswith("--autoplay") for flag in command)
