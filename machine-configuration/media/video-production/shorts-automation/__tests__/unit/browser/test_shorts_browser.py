from pathlib import Path
from unittest.mock import Mock

import pytest
from shorts_browser import browser_arguments


@pytest.fixture
def browser_process(monkeypatch):
    scope = Path.home() / ".local/share/opencli/profiles/shorts"
    instance = {
        "profileName": "shorts",
        "scope": str(scope),
        "id": "owned-job",
        "pid": 123,
    }
    monkeypatch.setenv("SHORTS_OPENCLI", "/bin/opencli")
    monkeypatch.setattr("shorts_browser.read_document", lambda path: instance)
    monkeypatch.setattr("shorts_browser.os.kill", Mock())
    status = {"managedJobId": "owned-job", "extensionConnected": True}
    monkeypatch.setattr(
        "shorts_browser.daemon_status",
        lambda: status,
    )
    return instance, status


def test_browser_action_uses_exact_persistent_profile(browser_process):
    assert browser_arguments(
        ["state", "--tab", "video"], {"browser_profile": "shorts"}
    ) == [
        "/bin/opencli",
        "browser",
        "--session",
        "shorts-production",
        "state",
        "--tab",
        "video",
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["instance", "start"],
        ["profiles"],
        ["open", "--server=http://other"],
        ["open", "--profile", "other"],
        ["open", "--session=other"],
        [],
    ],
)
def test_profile_changes_and_transport_override_are_rejected(arguments):
    with pytest.raises(ValueError, match="profile cannot be changed"):
        browser_arguments(arguments, {"browser_profile": "shorts"})


@pytest.mark.parametrize(
    "field, value", [("profileName", "other"), ("scope", "/unowned/profile")]
)
def test_wrong_profile_cannot_receive_action(browser_process, field, value):
    instance, status = browser_process
    instance[field] = value
    with pytest.raises(ValueError, match="exact logged-in"):
        browser_arguments(["state"], {"browser_profile": "shorts"})


def test_replaced_daemon_cannot_receive_action(browser_process):
    instance, status = browser_process
    status["managedJobId"] = "another-job"
    with pytest.raises(ValueError, match="exact logged-in"):
        browser_arguments(["state"], {"browser_profile": "shorts"})


def test_dead_owner_cannot_receive_action(browser_process, monkeypatch):
    monkeypatch.setattr("shorts_browser.os.kill", Mock(side_effect=ProcessLookupError))
    with pytest.raises(ValueError, match="exact logged-in"):
        browser_arguments(["state"], {"browser_profile": "shorts"})
