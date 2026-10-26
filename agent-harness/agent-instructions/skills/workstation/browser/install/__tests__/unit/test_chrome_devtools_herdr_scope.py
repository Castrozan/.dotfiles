import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_devtools_session as sessions


@pytest.fixture
def herdr_context(tmp_path, monkeypatch):
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_SESSION", "alpha")
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "alpha/herdr.sock"))
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")
    monkeypatch.setenv("CODEX_THREAD_ID", "same-thread")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    return tmp_path


def test_identical_pane_ids_in_distinct_sessions_are_isolated(
    herdr_context, monkeypatch
):
    first = sessions.ChromeDevtoolsSession.current(herdr_context)
    monkeypatch.setenv("HERDR_SESSION", "beta")
    second = sessions.ChromeDevtoolsSession.current(herdr_context)
    assert first.identifier != second.identifier
    assert first.pid_file != second.pid_file
    assert first.state_file != second.state_file


def test_same_session_name_with_different_endpoints_is_isolated(
    herdr_context, monkeypatch
):
    first = sessions.ChromeDevtoolsSession.current(herdr_context)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_context / "other/herdr.sock"))
    assert (
        first.identifier
        != sessions.ChromeDevtoolsSession.current(herdr_context).identifier
    )


@pytest.mark.parametrize(
    "name",
    ["", " ", "..", ".", "bad/name", "bad\\name", " bad", "bad\n", "a" * 65, "sessión"],
)
def test_invalid_session_never_falls_back_to_codex(herdr_context, monkeypatch, name):
    monkeypatch.setenv("HERDR_SESSION", name)
    with pytest.raises(RuntimeError, match="HERDR_SESSION"):
        sessions.ChromeDevtoolsSession.current(herdr_context)


def test_default_session_uses_injected_endpoint_when_name_is_absent(
    herdr_context, monkeypatch
):
    monkeypatch.setenv("HERDR_SESSION", "default")
    explicit = sessions.ChromeDevtoolsSession.current(herdr_context)
    monkeypatch.delenv("HERDR_SESSION")
    assert (
        explicit.identifier
        == sessions.ChromeDevtoolsSession.current(herdr_context).identifier
    )


@pytest.mark.parametrize(
    "variable,value",
    [
        ("HERDR_ENV", "0"),
        ("HERDR_PANE_ID", ""),
        ("HERDR_SOCKET_PATH", ""),
        ("HERDR_SOCKET_PATH", "relative.sock"),
    ],
)
def test_incomplete_herdr_context_fails_closed(
    herdr_context, monkeypatch, variable, value
):
    monkeypatch.setenv(variable, value)
    with pytest.raises(RuntimeError, match="Herdr"):
        sessions.ChromeDevtoolsSession.current(herdr_context)


def test_missing_session_and_endpoint_cannot_adopt_legacy_pane_scope(
    herdr_context, monkeypatch
):
    monkeypatch.delenv("HERDR_SESSION")
    monkeypatch.delenv("HERDR_SOCKET_PATH")
    with pytest.raises(RuntimeError, match="Herdr"):
        sessions.ChromeDevtoolsSession.current(herdr_context)


def test_namespaced_scope_never_matches_legacy_pane_scope(herdr_context):
    legacy = hashlib.sha256(b"HERDR_PANE_ID:w1:p2").hexdigest()[:32]
    assert sessions.ChromeDevtoolsSession.current(herdr_context).identifier != legacy


@pytest.mark.parametrize(
    "variable", ["HERDR_ENV", "HERDR_PANE_ID", "HERDR_SOCKET_PATH"]
)
def test_missing_required_context_is_not_a_codex_fallback(
    herdr_context, monkeypatch, variable
):
    monkeypatch.delenv(variable)
    with pytest.raises(RuntimeError, match="Herdr"):
        sessions.ChromeDevtoolsSession.current(herdr_context)


@pytest.mark.parametrize(
    "name", ["default", "work.1", "_scratch", "-scratch", "...", "a" * 64]
)
def test_native_valid_session_names_have_stable_scopes(
    herdr_context, monkeypatch, name
):
    monkeypatch.setenv("HERDR_SESSION", name)
    first = sessions.ChromeDevtoolsSession.current(herdr_context)
    assert first.automatic_cleanup
    assert (
        first.identifier
        == sessions.ChromeDevtoolsSession.current(herdr_context).identifier
    )
