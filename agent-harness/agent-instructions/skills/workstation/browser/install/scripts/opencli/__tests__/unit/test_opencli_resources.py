import importlib
import json
import stat
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def resources(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    module = importlib.import_module("opencli_resources")
    extension = tmp_path / "extension/dist"
    extension.mkdir(parents=True)
    (extension / "background.js").write_text("new WebSocket(DAEMON_WS_URL)")
    extension.parent.chmod(0o555)
    for key, value in {
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
        "OPENCLI_EXTENSION": str(extension.parent),
        "OPENCLI_NODE": "node",
        "OPENCLI_DAEMON": "daemon.js",
        "OPENCLI_BROWSER": "chromium",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(module, "require_unused_port", Mock())
    monkeypatch.setattr(module, "wait_for_bridge", Mock())
    owner = importlib.import_module("opencli_owner")
    monkeypatch.setattr(owner, "owner_connection", SimpleNamespace(fileno=lambda: 0))
    monkeypatch.setattr(owner, "stop_process", Mock())
    monkeypatch.setattr(
        importlib.import_module("opencli_browser"), "close_browser", Mock()
    )
    monkeypatch.setattr(
        owner.subprocess,
        "Popen",
        Mock(side_effect=[SimpleNamespace(pid=1), SimpleNamespace(pid=2)]),
    )
    return module


@pytest.fixture
def started_processes(resources):
    return importlib.import_module("opencli_owner").subprocess.Popen


@pytest.fixture
def stopped_processes(resources):
    return importlib.import_module("opencli_owner").stop_process


def test_job_owns_processes_hides_token_and_preserves_profile(
    resources, started_processes, stopped_processes
):
    with resources.browser_job("research") as environment:
        profile = resources.profile_directory("research")
        (profile / "saved-session").write_text("retained")
        extension = profile / "OpenCLIBridge/dist/background.js"
        token = started_processes.call_args_list[0].kwargs["env"][
            "OPENCLI_BRIDGE_TOKEN"
        ]
        assert (
            json.loads((extension.parent.parent / "job-token.json").read_text())[
                "token"
            ]
            == token
        )
        assert token not in extension.read_text()
        assert environment["OPENCLI_BRIDGE_TOKEN"] == token
        assert environment["OPENCLI_JOB_SCOPE"] == str(profile)
        assert stat.S_IMODE(extension.stat().st_mode) == 0o600
        assert stat.S_IMODE(profile.stat().st_mode) == 0o700
    assert (profile / "saved-session").read_text() == "retained"
    assert not (profile / "OpenCLIBridge").exists()
    assert [call.args[0].pid for call in stopped_processes.call_args_list] == [
        2,
        1,
    ]


def test_failed_start_releases_every_owned_resource(resources, stopped_processes):
    resources.wait_for_bridge.side_effect = TimeoutError("not ready")
    with pytest.raises(TimeoutError), resources.browser_job("failure"):
        pytest.fail("A failed startup must not run the workflow")
    assert stopped_processes.call_count == 2
    assert not (resources.profile_directory("failure") / "OpenCLIBridge").exists()


def test_competing_job_cannot_interrupt_current_owner(
    resources, started_processes, stopped_processes
):
    with resources.browser_job("first"):
        with pytest.raises(RuntimeError, match="Another OpenCLI job"):
            with resources.browser_job("second"):
                pytest.fail("A competing job must not acquire the Bridge")
        assert stopped_processes.call_count == 0
        assert started_processes.call_count == 2


def test_occupied_port_is_not_adopted_or_stopped(
    resources, started_processes, stopped_processes
):
    resources.require_unused_port.side_effect = RuntimeError("already owned")
    with pytest.raises(RuntimeError), resources.browser_job("occupied"):
        pytest.fail("An existing service must not be adopted")
    started_processes.assert_not_called()
    stopped_processes.assert_not_called()


@pytest.mark.parametrize(
    "name", ["../outside", "/outside/profile", "", "a/b", "-option"]
)
def test_profile_cannot_escape_owned_directory(resources, name):
    with pytest.raises(ValueError):
        resources.profile_directory(name)


def test_workflow_failure_releases_owned_resources(resources, stopped_processes):
    with pytest.raises(ValueError), resources.browser_job("failure"):
        raise ValueError("workflow failed")
    assert stopped_processes.call_count == 2


def test_existing_endpoint_and_profile_cannot_redirect_job(resources, monkeypatch):
    for key in ("OPENCLI_CDP_ENDPOINT", "OPENCLI_CDP_TARGET", "OPENCLI_PROFILE"):
        monkeypatch.setenv(key, "unrelated-browser")
    with resources.browser_job("isolated") as environment:
        assert not any(
            key in environment
            for key in ("OPENCLI_CDP_ENDPOINT", "OPENCLI_CDP_TARGET", "OPENCLI_PROFILE")
        )
