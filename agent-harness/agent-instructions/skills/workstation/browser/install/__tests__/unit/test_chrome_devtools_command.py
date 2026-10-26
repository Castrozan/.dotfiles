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


def test_attached_configuration_keeps_consent_and_recording(configuration):
    arguments = configuration.start_arguments("attached")
    assert "--autoConnect" in arguments
    assert "--headless=false" in arguments
    assert str(configuration.home_directory / ".config/chrome-global") in arguments
    assert "--experimentalScreencast" in arguments
    assert arguments[arguments.index("--experimentalFfmpegPath") + 1] == "/ffmpeg"
    assert not any("remote-debugging-port" in argument for argument in arguments)
    assert "--executablePath" not in arguments


def test_headless_start_uses_its_own_profile(configuration, monkeypatch):
    calls = []
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda arguments, **options: calls.append(arguments)
        or SimpleNamespace(returncode=0),
    )
    assert command.main(configuration, ["start", "--headless"]) == 0
    arguments = calls[0]
    assert "--autoConnect" not in arguments
    assert (
        str(configuration.home_directory / ".config/chrome-devtools-headless")
        in arguments
    )
    assert arguments[arguments.index("--executablePath") + 1] == "/chrome"


def test_headless_cold_tool_starts_once_then_reuses_worker(configuration, monkeypatch):
    starts = []
    invocations = []
    ChromeDevtoolsSession.current(configuration.home_directory).record_mode("headless")
    running = {"value": False}
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: running["value"])

    def start(arguments, **options):
        starts.append(arguments)
        running["value"] = True
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(command.subprocess, "run", start)
    monkeypatch.setattr(
        command.os, "execv", lambda executable, arguments: invocations.append(arguments)
    )
    command.main(configuration, ["list_pages"])
    command.main(configuration, ["take_snapshot", "1"])
    assert len(starts) == 1
    assert [arguments[3:] for arguments in invocations] == [
        ["list_pages"],
        ["take_snapshot", "1"],
    ]


def test_cleanup_removes_only_the_owning_scope(configuration, monkeypatch):
    first = ChromeDevtoolsSession.current(configuration.home_directory)
    first.record_mode("attached")
    monkeypatch.setenv("HERDR_PANE_ID", "other-pane")
    second = ChromeDevtoolsSession.current(configuration.home_directory)
    second.record_mode("headless")
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: False)
    calls = []
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda arguments, **options: calls.append(arguments)
        or SimpleNamespace(returncode=0),
    )
    assert command.main(configuration, ["cleanup"]) == 0
    assert first.state_file.exists()
    assert not second.state_file.exists()
    assert calls == [
        [configuration.upstream_executable, "--sessionId", second.identifier, "stop"]
    ]


def test_unused_cleanup_does_not_start_a_process(configuration, monkeypatch):
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *arguments, **options: pytest.fail("spawned a worker"),
    )
    assert command.main(configuration, ["cleanup"]) == 0
    assert not ChromeDevtoolsSession.current(
        configuration.home_directory
    ).directory.exists()


def test_failed_cleanup_retains_ownership_for_retry(configuration, monkeypatch):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    session.record_mode("headless")
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(returncode=7),
    )
    assert command.main(configuration, ["cleanup"]) == 7
    assert session.state_file.exists()


def test_start_failure_prevents_tool_execution(configuration, monkeypatch):
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: False)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(returncode=9),
    )
    monkeypatch.setattr(
        command.os, "execv", lambda *arguments: pytest.fail("executed a browser tool")
    )
    ChromeDevtoolsSession.current(configuration.home_directory).record_mode("headless")
    assert command.main(configuration, ["list_pages"]) == 9
    assert ChromeDevtoolsSession.current(
        configuration.home_directory
    ).state_file.exists()


@pytest.mark.parametrize("operation", ["start", "list_pages"])
def test_agent_cannot_start_an_unapproved_attached_connection(
    configuration, monkeypatch, operation
):
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "project-manager")
    monkeypatch.setattr(ChromeDevtoolsSession, "running", lambda self: False)
    started = []
    executed = []
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda arguments, **options: started.append(arguments)
        or SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        command.os, "execv", lambda executable, arguments: executed.append(arguments)
    )
    with pytest.raises(RuntimeError, match="Run connect"):
        command.main(configuration, [operation])
    assert started == []
    assert executed == []


def test_help_never_starts_a_worker(configuration, monkeypatch):
    calls = []
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *arguments, **options: pytest.fail("started a worker"),
    )
    monkeypatch.setattr(
        command.os, "execv", lambda executable, arguments: calls.append(arguments)
    )
    command.main(configuration, ["screencast_start", "--help"])
    assert calls[0][-2:] == ["screencast_start", "--help"]
    assert not ChromeDevtoolsSession.current(
        configuration.home_directory
    ).state_file.exists()


def test_private_session_override_is_rejected(configuration):
    with pytest.raises(ValueError, match="ownership is managed automatically"):
        command.main(configuration, ["--sessionId", "another-owner", "stop"])


@pytest.mark.parametrize(
    "arguments, expected",
    [
        (["--headless"], True),
        (["--headless=false"], False),
        (["--headless", "false"], False),
        (["--headless", "--no-headless"], False),
    ],
)
def test_headless_boolean_arguments(arguments, expected):
    assert command.headless_requested(arguments) is expected
