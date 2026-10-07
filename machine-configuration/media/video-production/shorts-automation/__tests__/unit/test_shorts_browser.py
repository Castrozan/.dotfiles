import json
from types import SimpleNamespace

import pytest

from shorts_browser import browser_arguments


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
    with pytest.raises(ValueError, match="profile cannot be changed"):
        browser_arguments(arguments, browser_configuration())


@pytest.mark.parametrize(
    ("profile", "url"),
    [
        ("another-profile", "http://127.0.0.1:9868"),
        ("authorized-profile", "http://remote"),
    ],
)
def test_wrong_profile_or_endpoint_cannot_receive_action(monkeypatch, profile, url):
    browser_process(monkeypatch, profile, url)
    with pytest.raises(ValueError, match="exact logged-in"):
        browser_arguments(["upload", "video.mp4"], browser_configuration())
