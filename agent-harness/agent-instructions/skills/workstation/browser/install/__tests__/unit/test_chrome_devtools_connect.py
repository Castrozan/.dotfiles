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

    assert connection.connect(SimpleNamespace(), session, [], forbidden, forbidden) == 0


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
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: True)

    def failed_request(*arguments):
        raise RuntimeError("request failed")

    monkeypatch.setattr(connection, "request_pages", failed_request)
    with pytest.raises(RuntimeError, match="request failed"):
        connection.connect(
            SimpleNamespace(), session, [], lambda *args: 0, lambda *args, **kwargs: 7
        )
    assert "Owned worker cleanup failed" in capsys.readouterr().out
