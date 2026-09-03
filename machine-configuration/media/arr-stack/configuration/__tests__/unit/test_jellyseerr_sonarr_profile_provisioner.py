import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import jellyseerr_sonarr_profile_provisioner


def test_routes_standard_and_anime_requests_to_named_profiles(monkeypatch):
    requests = []

    def request_json(method, url, api_key, body=None):
        requests.append((method, url, api_key, body))
        if method == "GET":
            return [
                {
                    "id": 0,
                    "name": "Sonarr",
                    "activeDirectory": "/data/media/tv",
                    "activeProfileId": 6,
                    "activeProfileName": "Old",
                }
            ]
        return body

    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner, "request_json", request_json
    )
    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner,
        "get_resource_list",
        lambda base_url, api_key, resource: [
            {"id": 8, "name": "HD - Original Language"},
            {"id": 9, "name": "HD - English Captions"},
        ],
    )
    outcomes = jellyseerr_sonarr_profile_provisioner.provision_sonarr_profiles(
        "http://jellyseerr",
        "jellyseerr-key",
        "http://sonarr/api/v3",
        "sonarr-key",
        [
            {
                "name": "Sonarr",
                "standardProfileName": "HD - Original Language",
                "animeProfileName": "HD - English Captions",
            }
        ],
        False,
    )
    assert outcomes == ["updated"]
    method, url, api_key, body = requests[-1]
    assert method == "PUT"
    assert url == "http://jellyseerr/api/v1/settings/sonarr/0"
    assert api_key == "jellyseerr-key"
    assert "id" not in body
    assert body["activeProfileId"] == 8
    assert body["activeProfileName"] == "HD - Original Language"
    assert body["activeAnimeProfileId"] == 9
    assert body["activeAnimeProfileName"] == "HD - English Captions"
    assert body["activeAnimeDirectory"] == "/data/media/tv"


def test_leaves_matching_route_unchanged(monkeypatch):
    writes = []
    route = {
        "id": 0,
        "name": "Sonarr",
        "activeDirectory": "/data/media/tv",
        "activeProfileId": 8,
        "activeProfileName": "HD - Original Language",
        "activeAnimeProfileId": 9,
        "activeAnimeProfileName": "HD - English Captions",
        "activeAnimeDirectory": "/data/media/tv",
    }
    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner,
        "request_json",
        lambda method, url, api_key, body=None: [route]
        if method == "GET"
        else writes.append(body),
    )
    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner,
        "get_resource_list",
        lambda base_url, api_key, resource: [
            {"id": 8, "name": "HD - Original Language"},
            {"id": 9, "name": "HD - English Captions"},
        ],
    )
    outcomes = jellyseerr_sonarr_profile_provisioner.provision_sonarr_profiles(
        "j",
        "jk",
        "s",
        "sk",
        [
            {
                "name": "Sonarr",
                "standardProfileName": "HD - Original Language",
                "animeProfileName": "HD - English Captions",
            }
        ],
        False,
    )
    assert outcomes == ["unchanged"]
    assert writes == []


def test_reports_missing_profile_without_writing(monkeypatch):
    writes = []
    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner,
        "request_json",
        lambda method, url, api_key, body=None: [{"id": 0, "name": "Sonarr"}]
        if method == "GET"
        else writes.append(body),
    )
    monkeypatch.setattr(
        jellyseerr_sonarr_profile_provisioner,
        "get_resource_list",
        lambda base_url, api_key, resource: [
            {"id": 8, "name": "HD - Original Language"}
        ],
    )
    outcomes = jellyseerr_sonarr_profile_provisioner.provision_sonarr_profiles(
        "j",
        "jk",
        "s",
        "sk",
        [
            {
                "name": "Sonarr",
                "standardProfileName": "HD - Original Language",
                "animeProfileName": "Missing",
            }
        ],
        False,
    )
    assert outcomes == ["missing-profile"]
    assert writes == []
