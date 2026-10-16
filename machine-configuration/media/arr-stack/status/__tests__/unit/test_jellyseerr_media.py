import importlib
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/arr_media"))
media = importlib.import_module("jellyseerr_media")


def test_transport_impersonates_ordinary_requester_with_bounded_timeout(monkeypatch):
    observed = []

    def open_request(request, timeout):
        observed.append((request, timeout))
        return io.BytesIO(b'{"id":8,"status":2}')

    monkeypatch.setattr(media.urllib.request, "urlopen", open_request)
    client = media.JellyseerrMedia("secret", 2)
    client.request("POST", "/request", {"mediaType": "movie", "mediaId": 36657})
    request, timeout = observed[0]
    assert timeout == 20
    assert request.get_header("X-api-user") == "2"
    assert request.get_header("X-api-key") == "secret"
    assert json.loads(request.data) == {"mediaType": "movie", "mediaId": 36657}


@pytest.mark.parametrize(
    "users",
    [
        [],
        [{"id": 1, "jellyfinUsername": "lucas", "permissions": 160}],
    ],
)
def test_missing_requester_is_rejected(tmp_path, monkeypatch, users):
    settings = tmp_path / "config/jellyseerr/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"main": {"apiKey": "secret"}}))
    monkeypatch.setattr(media.JellyseerrMedia, "request", lambda *_: {"results": users})
    with pytest.raises(ValueError):
        media.public_requester(tmp_path)


@pytest.mark.parametrize("permissions", [2, 16, 16384, 8352])
def test_requester_permissions_are_checked_before_impersonation(
    tmp_path, monkeypatch, permissions
):
    settings = tmp_path / "config/jellyseerr/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"main": {"apiKey": "secret"}}))
    monkeypatch.setattr(
        media.JellyseerrMedia,
        "request",
        lambda *_: {
            "results": [
                {"id": 2, "jellyfinUsername": "lucas", "permissions": permissions}
            ]
        },
    )
    if permissions == 8352:
        assert media.public_requester(tmp_path).requester_id == 2
    else:
        with pytest.raises(ValueError):
            media.public_requester(tmp_path)


def test_search_encodes_input_and_discards_service_and_user_data(monkeypatch):
    paths = []

    def request(client, method, path):
        paths.append(path)
        return {
            "results": [
                {
                    "id": 36657,
                    "mediaType": "movie",
                    "title": "X-Men",
                    "releaseDate": "2000-07-12",
                    "mediaInfo": {"secret": "private"},
                    "requestedBy": {"email": "private"},
                },
                {"id": 1, "mediaType": "person", "name": "Actor"},
            ]
        }

    monkeypatch.setattr(media.JellyseerrMedia, "request", request)
    result = media.JellyseerrMedia("secret", 2).search("X-Men & $(reboot)")
    assert "query=X-Men+%26+%24%28reboot%29" in paths[0]
    assert result == [
        {
            "media_id": 36657,
            "media_type": "movie",
            "title": "X-Men",
            "original_title": None,
            "year": "2000",
        }
    ]


def test_status_hides_private_requests_and_availability():
    details = {
        "id": 1,
        "title": "Catalog title",
        "mediaInfo": {
            "status": 5,
            "requests": [
                {"id": 9, "requestedBy": {"id": 3, "email": "private"}, "status": 2}
            ],
        },
    }
    client = media.JellyseerrMedia("secret", 2)
    result = media.public_status(client, details, "movie")
    assert result["requests"] == []
    assert "availability" not in result
    assert "private" not in json.dumps(result)
    details["mediaInfo"]["requests"].append(
        {"id": 10, "requestedBy": {"id": 2}, "status": 2}
    )
    result = media.public_status(client, details, "movie")
    assert result["requests"] == [
        {"request_id": 10, "status": "approved", "seasons": []}
    ]
    assert result["availability"] == "available"
