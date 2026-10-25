import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_devtools_connect as connection
from chrome_devtools_request import verified_pages
from chrome_devtools_session import ChromeDevtoolsSession


def test_warm_connection_does_not_start_worker_or_native_helper(tmp_path, monkeypatch):
    session = ChromeDevtoolsSession("warm", tmp_path, True)
    configuration = SimpleNamespace(upstream_executable="/current/backend")
    session.record_mode("attached", configuration.upstream_executable)
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: True)
    monkeypatch.setattr(
        connection,
        "request_pages",
        lambda configuration, session, deadline, helper, stack: 0
        if helper is None
        else 9,
    )

    def forbidden(*args, **kwargs):
        pytest.fail("started or stopped a warm worker")

    assert connection.connect(configuration, session, [], forbidden, forbidden) == 0


@pytest.mark.parametrize(
    "output", ["Error: denied", "[]", '{"pages": []}', '{"message": "Error: denied"}']
)
def test_successful_exit_without_pages_is_not_a_connection(output):
    assert not verified_pages(output)


def test_unsupported_approval_does_not_start_a_request(tmp_path, monkeypatch):
    session = ChromeDevtoolsSession("unsupported", tmp_path, True)
    calls = []
    monkeypatch.setattr(
        connection,
        "request_pages",
        lambda *args: pytest.fail("requested browser access"),
    )
    with pytest.raises(RuntimeError, match="supported only"):
        connection.connect(
            SimpleNamespace(consent_helper=()),
            session,
            ["--approve-once", "token"],
            lambda *args: calls.append("start"),
            lambda *args, **kwargs: calls.append("stop"),
        )
    assert calls == []


def test_worker_cleanup_failure_is_reported(tmp_path, monkeypatch, capsys):
    session = ChromeDevtoolsSession("cleanup", tmp_path, True)
    configuration = SimpleNamespace(upstream_executable="/current/backend")
    session.record_mode("attached", configuration.upstream_executable)
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: True)

    def failed_request(*arguments):
        raise RuntimeError("request failed")

    monkeypatch.setattr(connection, "request_pages", failed_request)
    with pytest.raises(RuntimeError, match="request failed"):
        connection.connect(
            configuration, session, [], lambda *args: 0, lambda *args, **kwargs: 7
        )
    assert "Owned worker cleanup failed" in capsys.readouterr().out


def test_cold_connection_without_scoped_approval_never_requests_access(
    tmp_path, monkeypatch
):
    session = ChromeDevtoolsSession("no-grant", tmp_path, True)
    calls = []
    monkeypatch.setattr(
        connection, "request_pages", lambda *args: calls.append("request") or 0
    )
    with pytest.raises(RuntimeError, match="scoped approval"):
        connection.connect(
            SimpleNamespace(consent_helper=()),
            session,
            [],
            lambda *args, **kwargs: calls.append("start") or 0,
            lambda *args, **kwargs: calls.append("stop") or 0,
        )
    assert calls == []


@pytest.mark.parametrize("option", ["--approve-once", "--manual-once"])
def test_scoped_retry_restarts_only_its_owned_worker(tmp_path, monkeypatch, option):
    session = ChromeDevtoolsSession("approved-retry", tmp_path, True)
    running = {"value": True}
    calls = []
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: running["value"])

    def stop(*args, **kwargs):
        calls.append("stop")
        running["value"] = False
        return 0

    def start(*args, **kwargs):
        calls.append("start")
        return 0

    monkeypatch.setattr(
        connection, "connection_helper", lambda *args: calls.append("helper")
    )
    monkeypatch.setattr(
        connection, "request_pages", lambda *args: calls.append("request") or 0
    )
    arguments = [option, "token"] if option == "--approve-once" else [option]
    assert connection.connect(SimpleNamespace(), session, arguments, start, stop) == 0
    assert calls == ["stop", "helper", "start", "request"]


def test_manual_consent_rejects_headless_without_starting_tools(tmp_path):
    session = ChromeDevtoolsSession("headless", tmp_path, True)
    session.record_mode("headless")

    def forbidden(*args, **kwargs):
        pytest.fail("started an approval request")

    with pytest.raises(ValueError, match="headless"):
        connection.connect(
            SimpleNamespace(), session, ["--manual-once"], forbidden, forbidden
        )


def test_legacy_running_worker_is_not_reused_or_stopped(tmp_path, monkeypatch):
    session = ChromeDevtoolsSession("legacy", tmp_path, True)
    session.state_file.write_text('{"mode":"attached"}')
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: True)
    calls = []
    monkeypatch.setattr(
        connection, "request_pages", lambda *args: calls.append("request") or 0
    )
    with pytest.raises(RuntimeError, match="older attached worker"):
        connection.connect(
            SimpleNamespace(upstream_executable="/current/backend"),
            session,
            [],
            lambda *args, **kwargs: calls.append("start") or 0,
            lambda *args, **kwargs: calls.append("stop") or 0,
        )
    assert calls == []
