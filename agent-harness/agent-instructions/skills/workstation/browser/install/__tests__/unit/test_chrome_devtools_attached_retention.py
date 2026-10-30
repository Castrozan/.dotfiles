import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_devtools_command as command
from chrome_devtools_session import ChromeDevtoolsSession


@pytest.fixture
def configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("HERDR_PANE_ID", "browser-test-pane")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    return command.ChromeDevtoolsConfiguration(
        "/upstream/chrome-devtools", tmp_path, "/ffmpeg", "/chrome"
    )


def age_state_file(session, seconds):
    import os
    import time

    moment = time.time() - seconds
    os.utime(session.state_file, (moment, moment))


def stub_stop(monkeypatch, calls):
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: False)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda arguments, **options: calls.append(arguments)
        or SimpleNamespace(returncode=0),
    )


def test_cleanup_keeps_an_attached_worker_used_within_the_allowance(
    configuration, monkeypatch
):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("attached")
    age_state_file(session, 60)
    calls = []
    stub_stop(monkeypatch, calls)
    assert command.main(configuration, ["cleanup", "--keep-attached-for", "1800"]) == 0
    assert session.state_file.exists()
    assert calls == []


def test_cleanup_closes_an_attached_worker_idle_past_the_allowance(
    configuration, monkeypatch
):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("attached")
    age_state_file(session, 3600)
    calls = []
    stub_stop(monkeypatch, calls)
    assert command.main(configuration, ["cleanup", "--keep-attached-for", "1800"]) == 0
    assert not session.state_file.exists()
    assert len(calls) == 1


def test_cleanup_closes_a_headless_worker_whatever_its_idle_time(
    configuration, monkeypatch
):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("headless")
    calls = []
    stub_stop(monkeypatch, calls)
    assert command.main(configuration, ["cleanup", "--keep-attached-for", "1800"]) == 0
    assert not session.state_file.exists()


def test_plain_cleanup_still_closes_an_attached_worker(configuration, monkeypatch):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("attached")
    calls = []
    stub_stop(monkeypatch, calls)
    assert command.main(configuration, ["cleanup"]) == 0
    assert not session.state_file.exists()


def test_cleanup_rejects_an_allowance_that_is_not_a_number(configuration):
    ChromeDevtoolsSession.current(configuration.home_directory).record_mode("attached")
    with pytest.raises(ValueError, match="number of seconds"):
        command.main(configuration, ["cleanup", "--keep-attached-for", "soon"])


def test_using_the_browser_marks_the_worker_as_recently_used(
    configuration, monkeypatch
):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("attached", configuration.upstream_executable)
    age_state_file(session, 3600)
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: True)
    monkeypatch.setattr(command.os, "execv", lambda *arguments: 0)
    command.invoke_browser(configuration, session, ["list_pages"], "list_pages")
    assert session.idle_seconds() < 60
