import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from shorts_browser import browser_arguments
import shorts_browser_server
from shorts_browser_start import start_profile


def browser_configuration():
    return {"browser_profile": "shorts", "browser_profile_id": "authorized-profile"}


def browser_process(
    monkeypatch, profile="authorized-profile", url="http://127.0.0.1:9868"
):
    monkeypatch.setenv("SHORTS_PINCHTAB", "/bin/pinchtab")
    instance = {
        "profileId": profile,
        "profileName": "shorts",
        "status": "running",
        "url": url,
    }
    monkeypatch.setattr(
        "shorts_browser.subprocess.run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=0, stdout=json.dumps([instance])
        ),
    )


def test_browser_action_uses_exact_persistent_profile(monkeypatch):
    browser_process(monkeypatch)
    assert browser_arguments(["snap", "--tab", "video"], browser_configuration()) == [
        "/bin/pinchtab",
        "--server",
        "http://127.0.0.1:9868",
        "snap",
        "--tab",
        "video",
    ]


@pytest.mark.parametrize(
    "arguments",
    [["instance", "start"], ["profiles"], ["nav", "--server=http://other"], []],
)
def test_profile_changes_and_transport_override_are_rejected(arguments):
    configuration = browser_configuration()
    with pytest.raises(ValueError, match="profile cannot be changed"):
        browser_arguments(arguments, configuration)


@pytest.mark.parametrize(
    ("profile", "url"),
    [
        ("another-profile", "http://127.0.0.1:9868"),
        ("authorized-profile", "http://remote"),
    ],
)
def test_wrong_profile_or_endpoint_cannot_receive_action(monkeypatch, profile, url):
    browser_process(monkeypatch, profile, url)
    configuration = browser_configuration()
    with pytest.raises(ValueError, match="exact logged-in"):
        browser_arguments(["upload", "video.mp4"], configuration)


def test_invalid_configuration_cannot_start_a_default_browser(monkeypatch):
    monkeypatch.setenv("SHORTS_PINCHTAB", "/bin/pinchtab")
    monkeypatch.setenv("SHORTS_BROWSER_CONFIGURATION", "/owned/browser.json")
    monkeypatch.setattr(
        shorts_browser_server,
        "read_document",
        lambda path: {"server": {"token": "fixture-credential"}},
    )
    validate = Mock(side_effect=subprocess.CalledProcessError(1, "pinchtab"))
    execute = Mock()
    monkeypatch.setattr(shorts_browser_server.subprocess, "run", validate)
    monkeypatch.setattr(shorts_browser_server.os, "execve", execute)
    with pytest.raises(subprocess.CalledProcessError):
        shorts_browser_server.main()
    execute.assert_not_called()
    assert validate.call_args.args[0] == ["/bin/pinchtab", "config", "validate"]


@pytest.mark.parametrize("exists", [True, False])
def test_startup_uses_only_existing_authorized_profile(monkeypatch, exists):
    profile = {"id": "authorized-profile", "name": "shorts", "pathExists": exists}
    run = Mock(return_value=SimpleNamespace(stdout=json.dumps([profile])))
    monkeypatch.setattr("shorts_browser_start.subprocess.run", run)
    configuration = browser_configuration()
    if not exists:
        with pytest.raises(ValueError, match="existing Shorts profile"):
            start_profile(configuration, "/bin/pinchtab")
        assert run.call_count == 1
        return
    start_profile(browser_configuration(), "/bin/pinchtab")
    assert run.call_args.args[0] == [
        "/bin/pinchtab",
        "instance",
        "start",
        "--profile=shorts",
        "--mode",
        "headless",
        "--port",
        "9868",
    ]
