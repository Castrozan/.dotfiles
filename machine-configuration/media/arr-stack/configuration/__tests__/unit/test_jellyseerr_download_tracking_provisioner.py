import sys
from pathlib import Path

import pytest

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import jellyseerr_download_tracking_provisioner
import provisioning_steps


@pytest.mark.parametrize("server_type", ["radarr", "sonarr"])
def test_enables_tracking_and_preserves_other_server_settings(monkeypatch, server_type):
    server = {
        "id": 0,
        "name": server_type.title(),
        "apiKey": "existing-server-key",
        "activeProfileId": 6,
        "activeDirectory": "/data/media/private",
        "syncEnabled": False,
        "enableAutomaticSearch": True,
    }
    original_server = dict(server)
    calls = []

    def request_json(method, url, api_key, body=None):
        calls.append((method, url, api_key, body))
        if method == "GET":
            return [server]
        server.update(body)
        return server

    monkeypatch.setattr(
        jellyseerr_download_tracking_provisioner, "request_json", request_json
    )
    outcomes = (
        jellyseerr_download_tracking_provisioner.provision_server_download_tracking(
            "http://jellyseerr", "jellyseerr-key", server_type, False
        )
    )
    assert outcomes == ["updated"]
    assert calls[-1] == (
        "PUT",
        f"http://jellyseerr/api/v1/settings/{server_type}/0",
        "jellyseerr-key",
        {
            **{
                field: value
                for field, value in original_server.items()
                if field != "id"
            },
            "syncEnabled": True,
        },
    )
    calls.clear()
    outcomes = (
        jellyseerr_download_tracking_provisioner.provision_server_download_tracking(
            "http://jellyseerr", "jellyseerr-key", server_type, False
        )
    )
    assert outcomes == ["unchanged"]
    assert [call[0] for call in calls] == ["GET"]


def test_dry_run_reads_servers_without_writing(monkeypatch):
    calls = []

    def request_json(method, url, api_key, body=None):
        calls.append(method)
        return [{"id": 0, "name": "Radarr", "syncEnabled": False}]

    monkeypatch.setattr(
        jellyseerr_download_tracking_provisioner, "request_json", request_json
    )
    assert jellyseerr_download_tracking_provisioner.provision_server_download_tracking(
        "http://jellyseerr", "key", "radarr", True
    ) == ["would-update"]
    assert calls == ["GET"]


def test_missing_servers_are_not_created(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_download_tracking_provisioner,
        "request_json",
        lambda method, url, api_key, body=None: [],
    )
    assert (
        jellyseerr_download_tracking_provisioner.provision_server_download_tracking(
            "http://jellyseerr", "key", "radarr", False
        )
        == []
    )


def test_missing_api_key_fails_before_any_server_request(monkeypatch):
    calls = []
    monkeypatch.setattr(
        provisioning_steps,
        "provision_server_download_tracking",
        lambda *arguments: calls.append(arguments),
    )
    with pytest.raises(RuntimeError, match="jellyseerr api key unavailable"):
        provisioning_steps.provision_jellyseerr_download_tracking_step(
            {"jellyseerr_api_key": ""}, {"app": "radarr"}, False
        )
    assert calls == []
